"""Production settings for the Whisper Transcriber API."""

import os
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, Field


PLACEHOLDER_SENTINELS = {
    "change-me",
    "changeme",
    "default",
    "placeholder",
    "example",
    "sample",
    "localtest",
}


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
    database_url: str = Field(...)
    db_url: str = Field(...)

    # Security settings - REQUIRED
    secret_key: str = Field(...)
    jwt_secret_key: str = Field(...)
    admin_bootstrap_password: str = Field(...)
    redis_password: str = Field(...)

    # Backend selection
    job_queue_backend: str = "thread"
    storage_backend: str = "filesystem"

    # Dormant feature toggles
    multi_user_mode_enabled: bool = False
    legacy_user_header_enabled: bool = False
    container_builds_enabled: bool = False

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
    backup_scheduler_enabled: bool = True

    # Queue settings
    redis_url: str = Field(...)
    celery_broker_url: str = Field(...)
    celery_result_backend: str = Field(...)

    # Observability
    metrics_token: str | None = None

    # Logging
    log_level: str = "INFO"


def _require_env(name: str, description: str) -> str:
    """Return a non-placeholder environment variable.

    Args:
        name: Environment variable name to fetch.
        description: Human-readable description used in error messages.

    Raises:
        RuntimeError: When the variable is unset or contains a placeholder value.
    """

    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} ({description}) must be provided via an environment variable.")

    if value.lower() in PLACEHOLDER_SENTINELS:
        raise RuntimeError(
            f"{name} ({description}) is using an insecure placeholder value. Provide a rotated secret."
        )

    return value


def _load_required_secrets() -> Dict[str, str]:
    """Load and validate the mandatory runtime secrets."""

    required = {
        "SECRET_KEY": "application signing key",
        "JWT_SECRET_KEY": "JWT signing key",
        "ADMIN_BOOTSTRAP_PASSWORD": "bootstrap administrator password",
        "DATABASE_URL": "database connection string",
        "REDIS_URL": "Redis connection string",
    }

    return {name: _require_env(name, description) for name, description in required.items()}


def _load_optional_secret(name: str) -> str | None:
    """Load an optional secret, validating that placeholders are not used."""

    value = os.getenv(name)
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    if stripped.lower() in PLACEHOLDER_SENTINELS:
        raise RuntimeError(
            f"{name} is using an insecure placeholder value. Provide a rotated secret."
        )

    return stripped


def _get_bool_env(name: str, default: bool) -> bool:
    """Read an environment variable as a boolean."""

    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    """Load settings from environment variables."""

    secrets = _load_required_secrets()

    database_dsn = secrets["DATABASE_URL"]
    redis_url = secrets["REDIS_URL"]

    celery_broker_url = os.getenv("CELERY_BROKER_URL", redis_url)
    celery_result_backend = os.getenv("CELERY_RESULT_BACKEND", redis_url)

    debug = _get_bool_env("DEBUG", False)
    environment = os.getenv("ENVIRONMENT") or ("development" if debug else "production")

    return Settings(
        secret_key=secrets["SECRET_KEY"],
        jwt_secret_key=secrets["JWT_SECRET_KEY"],
        admin_bootstrap_password=secrets["ADMIN_BOOTSTRAP_PASSWORD"],
        redis_password=_require_env("REDIS_PASSWORD", "Redis password"),
        database_url=database_dsn,
        db_url=database_dsn,
        redis_url=redis_url,
        celery_broker_url=celery_broker_url,
        celery_result_backend=celery_result_backend,
        metrics_token=_load_optional_secret("METRICS_TOKEN"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        debug=debug,
        environment=environment,
        backup_scheduler_enabled=os.getenv("BACKUP_SCHEDULER_ENABLED", "true").lower()
        not in {"false", "0", "no"},
        multi_user_mode_enabled=_get_bool_env("MULTI_USER_MODE_ENABLED", False),
        legacy_user_header_enabled=_get_bool_env("LEGACY_USER_HEADER_ENABLED", False),
        container_builds_enabled=_get_bool_env("CONTAINER_BUILDS_ENABLED", False),
    )


# Global settings instance
settings = load_settings()
