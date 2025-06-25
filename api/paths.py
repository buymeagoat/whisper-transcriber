from __future__ import annotations

from pathlib import Path

from api.settings import settings
from api.services.storage import LocalStorage, CloudStorage, Storage

ROOT = Path(__file__).parent
BASE_DIR = ROOT.parent


def _init_storage() -> Storage:
    if settings.storage_backend == "local":
        return LocalStorage(BASE_DIR)
    elif settings.storage_backend == "cloud":
        return CloudStorage()
    else:
        raise ValueError(f"Unknown STORAGE_BACKEND: {settings.storage_backend}")


storage = _init_storage()

UPLOAD_DIR = storage.upload_dir
TRANSCRIPTS_DIR = storage.transcripts_dir
MODEL_DIR = BASE_DIR / "models"
LOG_DIR = storage.log_dir
