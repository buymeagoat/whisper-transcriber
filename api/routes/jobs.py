from fastapi import APIRouter, UploadFile, File, Form, Request, status
from fastapi.responses import FileResponse, HTMLResponse
from datetime import datetime
from pathlib import Path
import shutil
import uuid

from api.errors import ErrorCode, http_error
from api.models import JobStatusEnum
from api.app_state import LOCAL_TZ, handle_whisper
from api.services.jobs import (
    create_job,
    list_jobs as service_list_jobs,
    get_job as service_get_job,
    get_metadata as service_get_metadata,
    delete_job as service_delete_job,
    update_job_status,
)
from api.paths import UPLOAD_DIR, TRANSCRIPTS_DIR, LOG_DIR

router = APIRouter()


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
async def submit_job(file: UploadFile = File(...), model: str = Form("base")):
    job_id = uuid.uuid4().hex
    saved = f"{job_id}_{file.filename}"
    upload_path = UPLOAD_DIR / saved
    job_dir = TRANSCRIPTS_DIR / job_id

    try:
        with upload_path.open("wb") as dst:
            shutil.copyfileobj(file.file, dst)
    except Exception:
        raise http_error(ErrorCode.FILE_SAVE_FAILED)

    ts = datetime.now(LOCAL_TZ)
    create_job(job_id, file.filename, saved, model, ts)

    handle_whisper(job_id, upload_path, job_dir, model)
    return {"job_id": job_id}


@router.get("/jobs")
def list_jobs():
    jobs = service_list_jobs()
    return [
        {
            "id": j.id,
            "original_filename": j.original_filename,
            "model": j.model,
            "created_at": j.created_at.isoformat(),
            "updated": j.updated_at.isoformat(),
            "status": j.status.value,
        }
        for j in jobs
    ]


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)
    return {
        "id": job.id,
        "original_filename": job.original_filename,
        "model": job.model,
        "created_at": job.created_at.isoformat(),
        "updated": job.updated_at.isoformat(),
        "status": job.status.value,
    }


@router.get("/metadata/{job_id}")
def get_metadata(job_id: str):
    metadata = service_get_metadata(job_id)
    if not metadata:
        raise http_error(ErrorCode.JOB_NOT_FOUND)
    return {
        "tokens": metadata.tokens,
        "duration": metadata.duration,
        "abstract": metadata.abstract,
        "sample_rate": metadata.sample_rate,
        "generated_at": metadata.generated_at.isoformat(),
    }


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    saved_filename = job.saved_filename
    transcript_dir = TRANSCRIPTS_DIR / job_id
    upload_path = UPLOAD_DIR / saved_filename
    log_path = LOG_DIR / f"{job_id}.log"

    shutil.rmtree(transcript_dir, ignore_errors=True)

    try:
        upload_path.unlink()
    except FileNotFoundError:
        pass

    try:
        log_path.unlink()
    except FileNotFoundError:
        pass

    service_delete_job(job_id)
    return {"status": "deleted"}


@router.get("/jobs/{job_id}/download")
def download_transcript(job_id: str):
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    if not job.transcript_path:
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    srt_path = Path(job.transcript_path)
    if not srt_path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    original_name = Path(job.original_filename).stem + ".srt"
    return FileResponse(path=srt_path, media_type="text/plain", filename=original_name)


@router.get("/transcript/{job_id}/view", response_class=HTMLResponse)
def transcript_view(job_id: str, request: Request):
    job = service_get_job(job_id)
    if not job:
        return HTMLResponse(
            content=f"<h2>Job not found: {job_id}</h2>", status_code=404
        )

    transcript_path = job.transcript_path

    if not transcript_path:
        return HTMLResponse(
            content=f"<h2>No transcript available for job {job_id}</h2>",
            status_code=404,
        )

    transcript_file = Path(transcript_path)
    if not transcript_file.exists():
        return HTMLResponse(
            content=f"<h2>Transcript file not found at {transcript_file}</h2>",
            status_code=404,
        )

    transcript_text = transcript_file.read_text(encoding="utf-8")
    html = f"""
    <html>
      <head>
        <title>Transcript for {job_id}</title>
        <style>
          body {{ background: #111; color: #eee; font-family: monospace; padding: 2rem; }}
          pre {{ white-space: pre-wrap; word-wrap: break-word; }}
        </style>
      </head>
      <body>
        <h1>Transcript for Job ID: {job_id}</h1>
        <pre>{transcript_text}</pre>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/jobs/{job_id}/restart")
def restart_job(job_id: str):
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    saved_filename = job.saved_filename
    model = job.model
    upload_path = UPLOAD_DIR / saved_filename
    job_dir = TRANSCRIPTS_DIR / job_id

    if not upload_path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    shutil.rmtree(job_dir, ignore_errors=True)

    update_job_status(job_id, JobStatusEnum.QUEUED)

    handle_whisper(job_id, upload_path, job_dir, model)
    return {"status": "restarted"}
