from fastapi import APIRouter, UploadFile, File, Form, Request, status
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from datetime import datetime
from pathlib import Path
import shutil
import uuid

from api.errors import ErrorCode, http_error
from api.models import Job, JobStatusEnum, TranscriptMetadata
from api.orm_bootstrap import SessionLocal
from api.app_state import LOCAL_TZ
from api.app_state import (
    UPLOAD_DIR,
    TRANSCRIPTS_DIR,
    LOG_DIR,
    db_lock,
    handle_whisper,
)

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
    with db_lock:
        with SessionLocal() as db:
            job = Job(
                id=job_id,
                original_filename=file.filename,
                saved_filename=saved,
                model=model,
                created_at=ts,
                status=JobStatusEnum.QUEUED,
            )
            db.add(job)
            db.commit()

    handle_whisper(job_id, upload_path, job_dir, model)
    return {"job_id": job_id}


@router.get("/jobs")
def list_jobs():
    with SessionLocal() as db:
        jobs = db.query(Job).order_by(Job.created_at.desc()).all()
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
    with SessionLocal() as db:
        job = db.query(Job).filter_by(id=job_id).first()
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
    with SessionLocal() as db:
        metadata = db.query(TranscriptMetadata).filter_by(job_id=job_id).first()
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
    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
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

            db.delete(job)
            db.commit()

        return {"status": "deleted"}


@router.get("/jobs/{job_id}/download")
def download_transcript(job_id: str):
    with SessionLocal() as db:
        job = db.query(Job).filter_by(id=job_id).first()
        if not job:
            raise http_error(ErrorCode.JOB_NOT_FOUND)

        if not job.transcript_path:
            raise http_error(ErrorCode.FILE_NOT_FOUND)

        srt_path = Path(job.transcript_path)
        if not srt_path.exists():
            raise http_error(ErrorCode.FILE_NOT_FOUND)

        original_name = Path(job.original_filename).stem + ".srt"
        return FileResponse(
            path=srt_path, media_type="text/plain", filename=original_name
        )


@router.get("/transcript/{job_id}/view", response_class=HTMLResponse)
def transcript_view(job_id: str, request: Request):
    with SessionLocal() as db:
        job = db.query(Job).filter_by(id=job_id).first()
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
    with db_lock:
        with SessionLocal() as db:
            job = db.query(Job).filter_by(id=job_id).first()
            if not job:
                raise http_error(ErrorCode.JOB_NOT_FOUND)

            saved_filename = job.saved_filename
            model = job.model
            upload_path = UPLOAD_DIR / saved_filename
            job_dir = TRANSCRIPTS_DIR / job_id

            if not upload_path.exists():
                raise http_error(ErrorCode.FILE_NOT_FOUND)

            shutil.rmtree(job_dir, ignore_errors=True)

            job.status = JobStatusEnum.QUEUED
            db.commit()

    handle_whisper(job_id, upload_path, job_dir, model)
    return {"status": "restarted"}
