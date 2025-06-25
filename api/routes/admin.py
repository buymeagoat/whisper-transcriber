from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import io
import shutil
import zipfile
from pathlib import Path

import psutil

from api.errors import ErrorCode, http_error
from api.models import Job
from api.orm_bootstrap import SessionLocal
from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR, LOG_DIR
from api.app_state import db_lock

router = APIRouter(prefix="/admin")


@router.get("/files")
def list_admin_files():
    logs = sorted(f.name for f in LOG_DIR.glob("*") if f.is_file())
    uploads = sorted(f.name for f in UPLOAD_DIR.glob("*") if f.is_file())
    transcripts = sorted(
        str(f.relative_to(TRANSCRIPTS_DIR))
        for f in TRANSCRIPTS_DIR.rglob("*")
        if f.is_file()
    )
    return {"logs": logs, "uploads": uploads, "transcripts": transcripts}


@router.delete("/files")
def delete_admin_file(payload: dict):
    folder = payload.get("folder")
    filename = payload.get("filename")
    folder_map = {
        "logs": LOG_DIR,
        "uploads": UPLOAD_DIR,
        "transcripts": TRANSCRIPTS_DIR,
    }
    if folder not in folder_map or not filename:
        raise http_error(ErrorCode.FILE_SAVE_FAILED)
    target = folder_map[folder] / filename
    if not target.exists() or not target.is_file():
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    target.unlink()
    return {"status": "deleted"}


@router.post("/reset")
def reset_system():
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
    return {"status": "reset complete"}


@router.get("/download-all")
def download_all():
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


@router.get("/stats")
def admin_stats():
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": cpu_percent,
        "mem_used_mb": round(mem.used / (1024 * 1024), 1),
        "mem_total_mb": round(mem.total / (1024 * 1024), 1),
    }
