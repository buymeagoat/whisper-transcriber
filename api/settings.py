from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    db_url: str = Field(
        "postgresql+psycopg2://whisper:whisper@db:5432/whisper", env="DB_URL"
    )
    vite_api_host: str = Field("http://192.168.1.52:8000", env="VITE_API_HOST")
    log_level: str = Field("DEBUG", env="LOG_LEVEL")
    log_format: str = Field("plain", env="LOG_FORMAT")
    log_to_stdout: bool = Field(False, env="LOG_TO_STDOUT")
    log_max_bytes: int = Field(10_000_000, env="LOG_MAX_BYTES")
    log_backup_count: int = Field(3, env="LOG_BACKUP_COUNT")
    max_upload_size: int = Field(2 * 1024**3, env="MAX_UPLOAD_SIZE")
    db_connect_attempts: int = Field(10, env="DB_CONNECT_ATTEMPTS")
    broker_connect_attempts: int = Field(10, env="BROKER_CONNECT_ATTEMPTS")
    allow_registration: bool = Field(True, env="ALLOW_REGISTRATION")
    auth_username: str = Field("admin", env="AUTH_USERNAME")
    auth_password: str = Field("admin", env="AUTH_PASSWORD")
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    max_concurrent_jobs: int = Field(2, env="MAX_CONCURRENT_JOBS")
    job_queue_backend: str = Field("thread", env="JOB_QUEUE_BACKEND")
    storage_backend: str = Field("local", env="STORAGE_BACKEND")
    local_storage_dir: str = Field(
        default=str(Path(__file__).resolve().parent.parent), env="LOCAL_STORAGE_DIR"
    )
    whisper_bin: str = Field("whisper", env="WHISPER_BIN")
    whisper_language: str = Field("en", env="WHISPER_LANGUAGE")
    whisper_timeout_seconds: int = Field(0, env="WHISPER_TIMEOUT_SECONDS")
    model_dir: str = Field(
        default=str(Path(__file__).resolve().parent.parent / "models"),
        env="MODEL_DIR",
    )
    aws_access_key_id: str | None = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(None, env="AWS_SECRET_ACCESS_KEY")
    s3_bucket: str | None = Field(None, env="S3_BUCKET")
    celery_broker_url: str = Field(
        "amqp://guest:guest@broker:5672//", env="CELERY_BROKER_URL"
    )
    celery_backend_url: str = Field("rpc://", env="CELERY_BACKEND_URL")
    cleanup_enabled: bool = Field(True, env="CLEANUP_ENABLED")
    cleanup_days: int = Field(30, env="CLEANUP_DAYS")
    cleanup_interval_seconds: int = Field(86400, env="CLEANUP_INTERVAL_SECONDS")
    enable_server_control: bool = Field(False, env="ENABLE_SERVER_CONTROL")
    timezone: str = Field("UTC", env="TIMEZONE")
    cors_origins: str = Field("*", env="CORS_ORIGINS")
    openai_api_key: str | None = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-3.5-turbo", env="OPENAI_MODEL")

    # Not configurable via environment
    algorithm: str = "HS256"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


import logging
from pydantic import ValidationError

from api.exceptions import ConfigurationError

try:
    settings = Settings()
except ValidationError as exc:
    if any(err["loc"][0] == "secret_key" for err in exc.errors()):
        msg = "SECRET_KEY environment variable not set"
        logging.critical(msg)
    else:
        msg = f"Invalid configuration: {exc}"
        logging.critical(msg)
    raise ConfigurationError(msg) from exc
