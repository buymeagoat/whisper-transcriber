from __future__ import annotations

from pathlib import Path

from api.settings import settings
from api.services.storage import LocalStorage, CloudStorage, Storage

ROOT = Path(__file__).parent
BASE_DIR = ROOT.parent


def _init_storage() -> Storage:
    if settings.storage_backend == "local":
        return LocalStorage(Path(settings.local_storage_dir))
    elif settings.storage_backend == "cloud":
        if not settings.s3_bucket:
            raise ValueError("S3_BUCKET must be set for cloud storage")
        return CloudStorage(
            settings.s3_bucket,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    else:
        raise ValueError(f"Unknown STORAGE_BACKEND: {settings.storage_backend}")


storage = _init_storage()

UPLOAD_DIR = storage.upload_dir
TRANSCRIPTS_DIR = storage.transcripts_dir
MODEL_DIR = BASE_DIR / "models"
LOG_DIR = storage.log_dir
