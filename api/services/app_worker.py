"""Celery tasks for handling background transcription jobs.

Unlike the original scaffolding, the worker now performs a full Whisper
inference cycle.  Jobs are promoted to ``processing`` when dequeued, the
configured checkpoint is loaded via :mod:`api.app_worker.bootstrap_model_assets`,
audio is transcribed with Whisper, and the resulting text is persisted to the
transcript directory.  Failures are captured in a per-job log file so that
operations teams can diagnose missing checkpoints or inference errors.
"""

from __future__ import annotations

import importlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from celery.utils.log import get_task_logger

from api.app_worker import bootstrap_model_assets, WhisperModelBootstrapError
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

    The task updates the ``jobs`` table to reflect the active state, resolves
    the requested Whisper checkpoint, executes ``model.transcribe`` against the
    uploaded audio, and persists the resulting transcript on disk.
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
        try:
            bootstrap_model_assets()
        except WhisperModelBootstrapError as exc:
            raise RuntimeError(f"Whisper model assets unavailable: {exc}") from exc

        model_name = job.model
        if not model_name:
            raise ValueError("Job is missing a Whisper model selection")

        model_path = storage.models_dir / f"{model_name}.pt"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")

        whisper = importlib.import_module("whisper")
        torch = importlib.import_module("torch")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        LOGGER.info("Loading Whisper model %s on %s", model_name, device)

        model = whisper.load_model(model_name, download_root=str(storage.models_dir))
        model.to(device)

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
