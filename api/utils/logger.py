"""
System logger utility for the Whisper Transcriber API.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional


SENSITIVE_ENV_VARS = (
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "REDIS_PASSWORD",
    "ADMIN_BOOTSTRAP_PASSWORD",
    "ADMIN_METRICS_TOKEN",
)


class EnvironmentSecretRedactor(logging.Filter):
    """Redact sensitive environment variable values from log messages."""

    def __init__(self, sensitive_map: Dict[str, str]):
        super().__init__()
        self._sensitive_map = {k: v for k, v in sensitive_map.items() if v}

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        sanitized = message

        for key, value in self._sensitive_map.items():
            if value and value in sanitized:
                sanitized = sanitized.replace(value, f"<redacted:{key}>")

        if sanitized != message:
            record.msg = sanitized
            record.args = ()

        return True

def get_system_logger(name: str = "whisper_api", level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured system logger.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Prepare redaction filter once so all handlers share the same rules
    redactor = EnvironmentSecretRedactor({key: os.getenv(key, "") for key in SENSITIVE_ENV_VARS})

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redactor)
    logger.addHandler(console_handler)

    # File handler (if logs directory exists)
    logs_dir = Path("logs")
    if logs_dir.exists():
        file_handler = logging.FileHandler(logs_dir / "api.log")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redactor)
        logger.addHandler(file_handler)

    return logger

def get_backend_logger(name: str = "whisper_backend") -> logging.Logger:
    """Get a logger for backend processes."""
    return get_system_logger(name)

def get_app_logger(name: str = "whisper_app") -> logging.Logger:
    """Get a logger for application-level events."""
    return get_system_logger(name)

def get_logger(name: str = "whisper_api") -> logging.Logger:
    """Alias for get_system_logger for backward compatibility."""
    return get_system_logger(name)
