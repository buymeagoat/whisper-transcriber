from fastapi import APIRouter, UploadFile, File, Form, status, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
import html
from datetime import datetime
from pathlib import Path
from functools import partial
import shutil
import uuid

from api.utils.logger import get_system_logger
from api.utils.model_validation import available_models

log = get_system_logger()
from api.app_state import backend_log

from api.errors import ErrorCode, http_error
from api.models import JobStatusEnum
from api.app_state import LOCAL_TZ, handle_whisper, job_queue
from api.services.jobs import (
    create_job,
    list_jobs as service_list_jobs,
    get_job as service_get_job,
    get_metadata as service_get_metadata,
    delete_job as service_delete_job,
    update_job_status,
    update_analysis,
)
from api.paths import storage, UPLOAD_DIR, TRANSCRIPTS_DIR, LOG_DIR
from api.schemas import (
    JobOut,
    JobListOut,
    MetadataOut,
    JobCreatedOut,
    StatusOut,
    AnalysisOut,
)
from api.services.analysis import analyze_text, detect_language, analyze_sentiment
from api.services.file_validation import file_validator, FileValidationError

router = APIRouter()


@router.post(
    "/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreatedOut
)
async def submit_job(
    file: UploadFile = File(...), model: str = Form("base")
) -> JobCreatedOut:
    # Validate model
    if model not in available_models():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid model"
        )
    
    # Comprehensive file validation
    try:
        safe_filename, detected_mime = await file_validator.validate_upload(file)
        backend_log.info(f"File validation passed: {safe_filename} ({detected_mime})")
    except FileValidationError as e:
        backend_log.warning(f"File validation failed for {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File validation failed: {str(e)}"
        )
    except Exception as e:
        backend_log.error(f"Unexpected error during file validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File validation error. Please try again."
        )
    
    job_id = uuid.uuid4().hex
    saved = f"{job_id}_{safe_filename}"
    try:
        upload_path = storage.save_upload(file.file, saved)
    except HTTPException:
        raise
    except OSError as e:
        backend_log.error(f"Failed to save upload '{saved}': {e}")
        raise http_error(ErrorCode.FILE_SAVE_FAILED) from e
    job_dir = storage.get_transcript_dir(job_id)

    ts = datetime.now(LOCAL_TZ)
    create_job(job_id, safe_filename, saved, model, ts)

    job_queue.enqueue(
        partial(handle_whisper, job_id, upload_path, job_dir, model, start_thread=False)
    )
    return JobCreatedOut(job_id=job_id)


@router.get("/jobs", response_model=list[JobListOut])
def list_jobs(search: str | None = None, status: str | None = None) -> list[JobListOut]:
    jobs = service_list_jobs(search, status)
    return [
        JobListOut(
            id=j.id,
            original_filename=j.original_filename,
            model=j.model,
            created_at=j.created_at,
            updated=j.updated_at,
            status=j.status,
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str) -> JobOut:
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)
    return JobOut(
        id=job.id,
        original_filename=job.original_filename,
        model=job.model,
        created_at=job.created_at,
        updated=job.updated_at,
        status=job.status,
    )


@router.get("/metadata/{job_id}", response_model=MetadataOut)
def get_metadata(job_id: str) -> MetadataOut:
    metadata = service_get_metadata(job_id)
    if not metadata:
        raise http_error(ErrorCode.JOB_NOT_FOUND)
    return MetadataOut(
        tokens=metadata.tokens,
        duration=metadata.duration,
        abstract=metadata.abstract,
        sample_rate=metadata.sample_rate,
        summary=metadata.summary,
        keywords=metadata.keywords,
        language=metadata.language,
        sentiment=metadata.sentiment,
        generated_at=metadata.generated_at,
    )


@router.delete("/jobs/{job_id}", response_model=StatusOut)
def delete_job(job_id: str) -> StatusOut:
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    saved_filename = job.saved_filename
    log_path = LOG_DIR / f"{job_id}.log"

    storage.delete_transcript_dir(job_id)

    storage.delete_upload(saved_filename)

    try:
        log_path.unlink()
    except FileNotFoundError:
        pass

    service_delete_job(job_id)
    return StatusOut(status="deleted")


@router.get("/jobs/{job_id}/download")
def download_transcript(job_id: str, format: str = "srt"):
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    if not job.transcript_path:
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    srt_path = Path(job.transcript_path)
    if not srt_path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    base_name = Path(job.original_filename).stem
    if format == "txt":
        from api.exporters import srt_to_txt

        content = srt_to_txt(srt_path)
        return Response(
            content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={base_name}.txt"},
        )
    if format == "vtt":
        from api.exporters import srt_to_vtt

        content = srt_to_vtt(srt_path)
        return Response(
            content,
            media_type="text/vtt",
            headers={"Content-Disposition": f"attachment; filename={base_name}.vtt"},
        )

    original_name = f"{base_name}.srt"
    return FileResponse(path=srt_path, media_type="text/plain", filename=original_name)


@router.post("/jobs/{job_id}/analyze", response_model=AnalysisOut)
def analyze_job(job_id: str) -> AnalysisOut:
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)
    if not job.transcript_path:
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    path = Path(job.transcript_path)
    if not path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)
    text = path.read_text(encoding="utf-8")
    summary, keywords = analyze_text(text)
    language = detect_language(text)
    sentiment = analyze_sentiment(text)
    update_analysis(job_id, summary, keywords, language, sentiment)
    return AnalysisOut(
        summary=summary,
        keywords=keywords,
        language=language,
        sentiment=sentiment,
    )


@router.get("/transcript/{job_id}/view", response_class=HTMLResponse)
def transcript_view(job_id: str):
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
        log.debug("Transcript file not found at %s", transcript_file)
        return HTMLResponse(
            content="<h2>Transcript file not found</h2>",
            status_code=404,
        )

    transcript_text = transcript_file.read_text(encoding="utf-8")
    html_content = f"""
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
        <pre>{html.escape(transcript_text)}</pre>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/jobs/{job_id}/restart", response_model=StatusOut)
def restart_job(job_id: str) -> StatusOut:
    job = service_get_job(job_id)
    if not job:
        raise http_error(ErrorCode.JOB_NOT_FOUND)

    saved_filename = job.saved_filename
    model = job.model
    upload_path = storage.get_upload_path(saved_filename)
    job_dir = storage.get_transcript_dir(job_id)

    if not upload_path.exists():
        raise http_error(ErrorCode.FILE_NOT_FOUND)

    storage.delete_transcript_dir(job_id)
    job_dir = storage.get_transcript_dir(job_id)

    update_job_status(job_id, JobStatusEnum.QUEUED)

    job_queue.enqueue(
        partial(handle_whisper, job_id, upload_path, job_dir, model, start_thread=False)
    )
    return StatusOut(status="restarted")
