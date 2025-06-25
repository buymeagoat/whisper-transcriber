from __future__ import annotations

from pathlib import Path

from api import config
from api.services.storage import LocalStorage, CloudStorage, Storage

ROOT = Path(__file__).parent
BASE_DIR = ROOT.parent


def _init_storage() -> Storage:
    if config.STORAGE_BACKEND == "local":
        return LocalStorage(BASE_DIR)
    elif config.STORAGE_BACKEND == "cloud":
        return CloudStorage()
    else:
        raise ValueError(f"Unknown STORAGE_BACKEND: {config.STORAGE_BACKEND}")


storage = _init_storage()

UPLOAD_DIR = storage.upload_dir
TRANSCRIPTS_DIR = storage.transcripts_dir
MODEL_DIR = BASE_DIR / "models"
LOG_DIR = storage.log_dir
