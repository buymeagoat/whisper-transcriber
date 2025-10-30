"""Production settings for the Whisper Transcriber API."""

import os
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from api.core.settings import get_core_settings


class Settings(BaseModel):
    """Production application settings."""

    # Basic app settings
    app_name: str = "Whisper Transcriber"
    version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001
    vite_api_host: str = "http://localhost:8001"

    # Database settings
    database_url: str = Field(default="sqlite:///./whisper.db")
    db_url: str = Field(default="sqlite:///./whisper.db")

    # Security settings - REQUIRED
    secret_key: str = Field(...)
    jwt_secret_key: str = Field(...)
    redis_password: str = Field(...)

    # Backend selection
    job_queue_backend: str = "thread"
    storage_backend: str = "filesystem"

    # Network settings
    allowed_hosts: List[str] = ["*"]
    cors_origins: str = "*"

    # File upload settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = [
        "audio/wav", "audio/x-wav", "audio/wave",
        "audio/mp3", "audio/mpeg", "audio/x-mp3",
        "audio/m4a", "audio/mp4", "audio/x-m4a",
        "audio/flac", "audio/x-flac",
    ]

    # Whisper settings
    default_model: str = "small"
    available_models: List[str] = ["tiny", "small", "medium", "large", "large-v3"]

    # Storage settings
    upload_dir: Path = Path("./storage/uploads")
    transcripts_dir: Path = Path("./storage/transcripts")
    models_dir: Path = Path("./models")
    cache_dir: Path = Path("./cache")

    # Queue settings
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Logging
    log_level: str = "INFO"


def load_settings() -> Settings:
    """Load settings from environment variables."""

    core_settings = get_core_settings()

    return Settings(
        secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
        redis_password=os.getenv("REDIS_PASSWORD", "change-me-in-production"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./whisper.db"),
        redis_url=core_settings.redis_url,
        celery_broker_url=core_settings.broker_url(),
        celery_result_backend=core_settings.result_backend(),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


# Global settings instance
settings = load_settings()
