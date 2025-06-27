# api/utils/logger.py

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from api.paths import LOG_DIR
from api.settings import settings


def get_logger(job_id: str) -> logging.Logger:
    """Returns a rotating per-job logger."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"{job_id}.log"

    logger = logging.getLogger(f"job_{job_id}")
    level = settings.log_level
    logger.setLevel(getattr(logging, level, logging.DEBUG))

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            f"[%(asctime)s] %(levelname)s [{job_id}]: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Optional: also log to console if enabled in .env
        if settings.log_to_stdout:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger


def get_system_logger(name="system") -> logging.Logger:
    """Logger for application-wide events not tied to a job."""
    log_path = LOG_DIR / "system.log"
    logger = logging.getLogger(name)
    level = settings.log_level
    logger.setLevel(getattr(logging, level, logging.DEBUG))
    logger.propagate = False

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [system]: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if settings.log_to_stdout:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger
