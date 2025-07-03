from __future__ import annotations

import logging

from api.exceptions import ConfigurationError

from api.settings import settings
from api.utils.logger import get_system_logger

log = get_system_logger()


def validate_config() -> None:
    """Validate required environment variables on startup."""
    issues: list[str] = []

    if not settings.secret_key:
        issues.append("SECRET_KEY environment variable not set")

    if not settings.db_url:
        issues.append("DB_URL environment variable not set")

    if settings.storage_backend == "cloud" and not settings.s3_bucket:
        issues.append("S3_BUCKET must be set when STORAGE_BACKEND=cloud")

    if issues:
        log.critical("Invalid configuration detected:")
        for item in issues:
            log.critical(" - %s", item)
        raise ConfigurationError("Invalid configuration")

    if log.isEnabledFor(logging.DEBUG):
        log.debug("Configuration validated")
