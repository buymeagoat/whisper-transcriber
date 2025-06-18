# api/utils/logger.py

import os
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))

def get_logger(job_id: str) -> logging.Logger:
    """Returns a rotating per-job logger."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"{job_id}.log")

    logger = logging.getLogger(f"job_{job_id}")
    level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    logger.setLevel(getattr(logging, level, logging.DEBUG))

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=10_000_000,
            backupCount=3,
            encoding="utf-8"
        )
        formatter = logging.Formatter(f"[%(asctime)s] %(levelname)s [{job_id}]: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Optional: also log to console if enabled in .env
        if os.getenv("LOG_TO_STDOUT", "false").lower() == "true":
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger

def get_system_logger(name="system") -> logging.Logger:
    """Logger for application-wide events not tied to a job."""
    log_path = os.path.join(LOG_DIR, "system.log")
    logger = logging.getLogger(name)
    level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    logger.setLevel(getattr(logging, level, logging.DEBUG))
    logger.propagate = False

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=10_000_000,
            backupCount=3,
            encoding="utf-8"
        )
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s [system]: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if os.getenv("LOG_TO_STDOUT", "false").lower() == "true":
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    return logger
