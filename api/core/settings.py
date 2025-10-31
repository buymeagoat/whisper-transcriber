"""Centralized application settings for database, Celery, and Redis integration."""


from __future__ import annotations
import os
from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus, urlencode

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    """Minimal core settings used by infrastructure components."""

    _env_file = os.environ.get("SETTINGS_ENV_FILE", ".env")
    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
        description="Primary Redis connection URI used by the platform.",
    )
    database_url: Optional[str] = Field(
        default=None,
        alias="DATABASE_URL",
        description=(
            "Fully qualified SQLAlchemy database URL. Overrides Postgres component "
            "settings when provided."
        ),
    )
    postgres_host: str = Field(
        default="localhost",
        alias="POSTGRES_HOST",
        description="Hostname of the primary PostgreSQL instance.",
    )
    postgres_port: int = Field(
        default=5432,
        alias="POSTGRES_PORT",
        description="Port used to connect to PostgreSQL.",
    )
    postgres_db: str = Field(
        default="whisper_transcriber",
        alias="POSTGRES_DB",
        description="Database name for the Whisper Transcriber service.",
    )
    postgres_user: str = Field(
        default="postgres",
        alias="POSTGRES_USER",
        description="Database user granted least-privilege access to the service schema.",
    )
    postgres_password: str = Field(
        default="",
        alias="POSTGRES_PASSWORD",
        description="Password for the PostgreSQL user. Optional when using IAM or peer authentication.",
    )
    postgres_sslmode: Optional[str] = Field(
        default="prefer",
        alias="POSTGRES_SSLMODE",
        description="SSL mode passed to libpq. Set to 'require' for production clusters.",
    )
    postgres_options: Optional[str] = Field(
        default=None,
        alias="POSTGRES_OPTIONS",
        description="Additional libpq options appended to the connection string.",
    )
    celery_broker_url: Optional[str] = Field(
        default=None,
        alias="CELERY_BROKER_URL",
        description="Broker URL for Celery. Defaults to Redis URL when unset.",
    )
    celery_result_backend: Optional[str] = Field(
        default=None,
        alias="CELERY_RESULT_BACKEND",
        description="Result backend URL for Celery. Defaults to Redis URL when unset.",
    )

    @model_validator(mode="after")
    def _populate_celery_defaults(self) -> "CoreSettings":
        """Ensure Celery broker and backend fall back to the Redis URL."""

        if self.celery_broker_url is None:
            self.celery_broker_url = self.redis_url
        if self.celery_result_backend is None:
            self.celery_result_backend = self.redis_url
        if not self.database_url:
            self.database_url = self._compose_postgres_dsn()
        return self

    def broker_url(self) -> str:
        """Return the broker URL, falling back to the Redis URL."""
        return self.celery_broker_url or self.redis_url

    def result_backend(self) -> str:
        """Return the result backend URL, falling back to the Redis URL."""
        return self.celery_result_backend or self.redis_url

    def database_dsn(self) -> str:
        """Return the primary SQLAlchemy database URL."""

        assert self.database_url is not None
        return self.database_url

    def _compose_postgres_dsn(self) -> str:
        """Construct a PostgreSQL connection string from component fields."""

        user = quote_plus(self.postgres_user)
        password = quote_plus(self.postgres_password) if self.postgres_password else ""
        credentials = user if not password else f"{user}:{password}"

        host_segment = f"{self.postgres_host}:{self.postgres_port}"
        auth_segment = f"{credentials}@" if credentials else ""
        base = f"postgresql://{auth_segment}{host_segment}/{self.postgres_db}"

        query_params = {}
        if self.postgres_sslmode:
            query_params["sslmode"] = self.postgres_sslmode
        if self.postgres_options:
            query_params["options"] = self.postgres_options

        return base if not query_params else f"{base}?{urlencode(query_params)}"


@lru_cache
def get_core_settings() -> CoreSettings:
    """Return a cached settings instance."""

    return CoreSettings()


__all__ = ["CoreSettings", "get_core_settings"]
