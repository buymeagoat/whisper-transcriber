"""Celery tasks for handling background transcription jobs.

This module integrates with the shared Celery application defined in
``api.worker`` and operates directly on the SQLAlchemy ``Job`` model.  The
tasks here are intentionally lightweight: they mark job progress in the
database, perform a very small stand-in "transcription" step so that the
pipeline can be exercised in development and automated tests, and persist a
log when failures occur.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import whisper
import torch

from celery.utils.log import get_task_logger

from api.models import Job, JobStatusEnum
from api.orm_bootstrap import SessionLocal
from api.paths import storage
from api.worker import celery_app
from api.utils.logger import bind_job_id, release_job_id


LOGGER = get_task_logger(__name__)


def _ensure_transcript_directory(job_id: str) -> Path:
    """Return the transcript directory for ``job_id`` ensuring it exists."""

    transcript_dir = storage.get_transcript_dir(job_id)
    transcript_dir.mkdir(parents=True, exist_ok=True)
    return transcript_dir


def _write_failure_log(job_id: str, error_message: str) -> str:
    """Persist a failure log for a job and return the file path as a string."""

    logs_dir = storage.logs_dir / "jobs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{job_id}.log"
    timestamp = datetime.utcnow().isoformat()
    log_path.write_text(f"[{timestamp}] {error_message}\n", encoding="utf-8")
    return str(log_path)


@celery_app.task(bind=True, name="api.services.app_worker.transcribe_audio")
def transcribe_audio(self, job_id: str, **kwargs: Any) -> Dict[str, Any]:  # pragma: no cover - exercised via Celery
    """Process a queued transcription job.

    The task updates the ``jobs`` table to reflect the active state, performs a
    lightweight placeholder transcription (writing the byte size to a text
    file), and records completion metadata.
    """

    session = SessionLocal()
    job_token = bind_job_id(job_id)
    job: Job | None = None

    try:
        job = session.get(Job, job_id)
        if job is None:
            LOGGER.error("Job %s does not exist", job_id)
            return {"job_id": job_id, "status": "missing"}

        job.status = JobStatusEnum.PROCESSING
        job.started_at = job.started_at or datetime.utcnow()
        job.updated_at = datetime.utcnow()
        session.commit()

        # Resolve the audio file path from either the task payload or the DB.
        audio_path = Path(kwargs.get("audio_path") or job.saved_filename)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found at {audio_path}")

        transcript_dir = _ensure_transcript_directory(job.id)
        transcript_path = transcript_dir / "transcript.txt"

        # Load Whisper model and perform transcription
        import whisper
        import torch

        # Get the model path based on the job's model selection
        model_path = storage.models_dir / f"{job.model}.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")

        # Load model with CUDA if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        LOGGER.info("Loading Whisper model %s on %s", job.model, device)
        
        model = whisper.load_model(str(model_path))
        model.to(device)

        # Transcribe the audio file
        LOGGER.info("Starting transcription for %s", job.original_filename)
        result = model.transcribe(str(audio_path))
        
        # Write the transcription result
        transcript_text = result["text"]
        transcript_path.write_text(transcript_text, encoding="utf-8")

        job.transcript_path = str(transcript_path)
        job.status = JobStatusEnum.COMPLETED
        job.finished_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        session.commit()

        LOGGER.info("Job %s completed", job.id)
        return {
            "job_id": job.id,
            "status": job.status.value,
            "transcript_path": job.transcript_path,
        }

    except Exception as exc:  # pragma: no cover - difficult to trigger reliably
        session.rollback()
        error_message = str(exc)
        LOGGER.exception("Job %s failed: %s", job_id, error_message)

        if job is not None:
            job.status = JobStatusEnum.FAILED
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            job.log_path = _write_failure_log(job.id, error_message)
            session.commit()

        # Re-raise so Celery marks the task as failed.
        raise

    finally:
        session.close()
        release_job_id(job_token)


@celery_app.task(name="api.services.app_worker.health_check")
def health_check() -> Dict[str, str]:
    """Simple health check task for smoke testing the worker."""

    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@celery_app.task(name="api.services.app_worker.smoke_transcription")
def smoke_transcription() -> Dict[str, str]:
    """A lightweight task that ensures the worker can execute queue jobs."""

    return {"status": "ok"}
