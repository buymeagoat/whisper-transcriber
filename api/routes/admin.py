from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import io
import shutil
import zipfile
from pathlib import Path

import os
import sys
import threading
import psutil

from api.errors import ErrorCode, http_error
from api.models import Job, JobStatusEnum
from api.orm_bootstrap import SessionLocal
from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR, LOG_DIR
from api.utils.db_lock import db_lock
import api.app_state as app_state
from api.services.job_queue import ThreadJobQueue
from api.schemas import FileListOut, StatusOut, AdminStatsOut, BrowseOut
from api.routes.auth import require_admin
from api.schemas import (
    CleanupConfigOut,
    CleanupConfigIn,
    ConcurrencyConfigOut,
    ConcurrencyConfigIn,
)
from api.services import config as config_service
from api.settings import settings

router = APIRouter(prefix="/admin")


@router.get("/files", response_model=FileListOut)
def list_admin_files(user=Depends(require_admin)) -> FileListOut:
    logs = sorted(f.name for f in LOG_DIR.glob("*") if f.is_file())
    uploads = sorted(f.name for f in UPLOAD_DIR.glob("*") if f.is_file())
    transcripts = sorted(
        str(f.relative_to(TRANSCRIPTS_DIR))
        for f in TRANSCRIPTS_DIR.rglob("*")
        if f.is_file()
    )
    return FileListOut(logs=logs, uploads=uploads, transcripts=transcripts)


@router.get("/browse", response_model=BrowseOut)
def browse_files(
    folder: str, path: str | None = None, user=Depends(require_admin)
) -> BrowseOut:
    folder_map = {
        "logs": LOG_DIR,
        "uploads": UPLOAD_DIR,
        "transcripts": TRANSCRIPTS_DIR,
    }
    if folder not in folder_map:
        raise http_error(ErrorCode.FILE_SAVE_FAILED)
    base = folder_map[folder].resolve()
    target = (base / path).resolve() if path else base
    try:
        target.relative_to(base)
    except ValueError:
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    if not target.exists() or not target.is_dir():
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    directories = []
    files = []
    for entry in target.iterdir():
        if entry.is_dir():
            directories.append(entry.name)
        elif entry.is_file():
            files.append(entry.name)
    return BrowseOut(directories=sorted(directories), files=sorted(files))


@router.delete("/files", response_model=StatusOut)
def delete_admin_file(payload: dict, user=Depends(require_admin)) -> StatusOut:
    folder = payload.get("folder")
    filename = payload.get("filename")
    folder_map = {
        "logs": LOG_DIR,
        "uploads": UPLOAD_DIR,
        "transcripts": TRANSCRIPTS_DIR,
    }
    if folder not in folder_map or not filename:
        raise http_error(ErrorCode.FILE_SAVE_FAILED)
    base = folder_map[folder].resolve()
    target = (base / filename).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    if not target.exists() or not target.is_file():
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    target.unlink()
    return StatusOut(status="deleted")


@router.post("/reset", response_model=StatusOut)
def reset_system(user=Depends(require_admin)) -> StatusOut:
    with db_lock:
        with SessionLocal() as db:
            db.query(Job).delete()
            db.commit()
    for directory in [UPLOAD_DIR, TRANSCRIPTS_DIR, LOG_DIR]:
        for file in directory.rglob("*"):
            if file.is_file():
                file.unlink()
            elif file.is_dir():
                shutil.rmtree(file, ignore_errors=True)
    return StatusOut(status="reset complete")


@router.get("/download-all")
def download_all(user=Depends(require_admin)):
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dir_path, prefix in [
            (LOG_DIR, "logs"),
            (UPLOAD_DIR, "uploads"),
            (TRANSCRIPTS_DIR, "transcripts"),
        ]:
            for file in dir_path.rglob("*"):
                if file.is_file():
                    arcname = f"{prefix}/{file.relative_to(dir_path)}"
                    zf.write(file, arcname)
    mem_zip.seek(0)
    return StreamingResponse(
        mem_zip,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=all_data.zip"},
    )


@router.get("/stats", response_model=AdminStatsOut)
def admin_stats(user=Depends(require_admin)) -> AdminStatsOut:
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    with SessionLocal() as db:
        completed_jobs = (
            db.query(Job).filter(Job.status == JobStatusEnum.COMPLETED).count()
        )
        times = (
            db.query(Job.started_at, Job.finished_at)
            .filter(
                Job.status == JobStatusEnum.COMPLETED,
                Job.started_at.isnot(None),
                Job.finished_at.isnot(None),
            )
            .all()
        )
        avg_job_time = (
            sum((f - s).total_seconds() for s, f in times) / len(times)
            if times
            else 0.0
        )
        queue_length = db.query(Job).filter(Job.status == JobStatusEnum.QUEUED).count()
    return AdminStatsOut(
        cpu_percent=cpu_percent,
        mem_used_mb=round(mem.used / (1024 * 1024), 1),
        mem_total_mb=round(mem.total / (1024 * 1024), 1),
        completed_jobs=completed_jobs,
        avg_job_time=round(avg_job_time, 2),
        queue_length=queue_length,
    )


@router.post("/shutdown", response_model=StatusOut)
def shutdown_server(user=Depends(require_admin)) -> StatusOut:
    """Shut down the running server process."""

    if not settings.enable_server_control:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server control disabled",
        )

    def _exit():
        os._exit(0)

    threading.Thread(target=_exit, daemon=True).start()
    return StatusOut(status="shutting down")


@router.post("/restart", response_model=StatusOut)
def restart_server(user=Depends(require_admin)) -> StatusOut:
    """Restart the running server process."""

    if not settings.enable_server_control:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Server control disabled",
        )

    def _restart():
        os.execv(sys.executable, [sys.executable] + sys.argv)

    threading.Thread(target=_restart, daemon=True).start()
    return StatusOut(status="restarting")


# ─── Cleanup Config Endpoints ────────────────────────────────────────────────


@router.get("/cleanup-config", response_model=CleanupConfigOut)
def get_cleanup_config() -> CleanupConfigOut:
    values = config_service.get_cleanup_config(
        settings.cleanup_enabled, settings.cleanup_days
    )
    return CleanupConfigOut(**values)


@router.post("/cleanup-config", response_model=CleanupConfigOut)
def update_cleanup_config(
    payload: CleanupConfigIn, user=Depends(require_admin)
) -> CleanupConfigOut:
    values = config_service.update_cleanup_config(
        payload.cleanup_enabled,
        payload.cleanup_days,
        default_enabled=settings.cleanup_enabled,
        default_days=settings.cleanup_days,
    )
    settings.cleanup_enabled = values["cleanup_enabled"]
    settings.cleanup_days = values["cleanup_days"]
    return CleanupConfigOut(**values)


# ─── Concurrency Config Endpoints ───────────────────────────────────────────


@router.get("/concurrency", response_model=ConcurrencyConfigOut)
def get_concurrency() -> ConcurrencyConfigOut:
    value = config_service.get_concurrency(settings.max_concurrent_jobs)
    return ConcurrencyConfigOut(max_concurrent_jobs=value)


@router.post("/concurrency", response_model=ConcurrencyConfigOut)
def update_concurrency(
    payload: ConcurrencyConfigIn, user=Depends(require_admin)
) -> ConcurrencyConfigOut:
    try:
        value = config_service.update_concurrency(payload.max_concurrent_jobs)
        settings.max_concurrent_jobs = value
        if settings.job_queue_backend == "thread" and isinstance(
            app_state.job_queue, ThreadJobQueue
        ):
            app_state.job_queue.resize(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ConcurrencyConfigOut(max_concurrent_jobs=value)
