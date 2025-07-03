from __future__ import annotations

from pathlib import Path

from api.settings import settings
from api.services.storage import LocalStorage, CloudStorage, Storage
import logging

from api.exceptions import InitError

ROOT = Path(__file__).parent
BASE_DIR = ROOT.parent


def init_storage() -> Storage:
    """Initialize the configured storage backend."""
    try:
        if settings.storage_backend == "local":
            return LocalStorage(Path(settings.local_storage_dir))
        if settings.storage_backend == "cloud":
            if not settings.s3_bucket:
                raise ValueError("S3_BUCKET must be set for cloud storage")
            return CloudStorage(
                settings.s3_bucket,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
        raise ValueError(f"Unknown STORAGE_BACKEND: {settings.storage_backend}")
    except Exception as exc:  # pragma: no cover - system exit
        message = f"Storage initialization failed: {exc}"
        logging.critical(message)
        raise InitError(message) from exc


storage = init_storage()

UPLOAD_DIR = storage.upload_dir
TRANSCRIPTS_DIR = storage.transcripts_dir
MODEL_DIR = Path(settings.model_dir)
LOG_DIR = storage.log_dir
