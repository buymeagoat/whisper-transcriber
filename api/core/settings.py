"""Centralized application settings for Celery and Redis integration."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    """Minimal core settings used by infrastructure components."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
        description="Primary Redis connection URI used by the platform.",
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
        return self

    def broker_url(self) -> str:
        """Return the broker URL, falling back to the Redis URL."""
        return self.celery_broker_url

    def result_backend(self) -> str:
        """Return the result backend URL, falling back to the Redis URL."""
        return self.celery_result_backend


@lru_cache
def get_core_settings() -> CoreSettings:
    """Return a cached settings instance."""

    return CoreSettings()


__all__ = ["CoreSettings", "get_core_settings"]
