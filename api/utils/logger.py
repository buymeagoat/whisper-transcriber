"""System logger utility for the Whisper Transcriber API."""

from __future__ import annotations

import json
import logging
import os
import sys
from contextvars import ContextVar, Token
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


SENSITIVE_ENV_VARS = (
    "SECRET_KEY",
    "JWT_SECRET_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "REDIS_PASSWORD",
    "ADMIN_BOOTSTRAP_PASSWORD",
    "ADMIN_METRICS_TOKEN",
)

LOG_RECORD_BUILTINS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "request_id",
    "job_id",
    "latency_ms",
}

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_job_id_ctx: ContextVar[Optional[str]] = ContextVar("job_id", default=None)
_latency_ctx: ContextVar[Optional[float]] = ContextVar("latency_ms", default=None)


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


class RequestIdFilter(logging.Filter):
    """Attach contextual identifiers to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        context_request_id = _request_id_ctx.get()
        if getattr(record, "request_id", None) is None:
            record.request_id = context_request_id
        context_job_id = _job_id_ctx.get()
        if getattr(record, "job_id", None) is None:
            record.job_id = context_job_id
        context_latency = _latency_ctx.get()
        if getattr(record, "latency_ms", None) is None:
            record.latency_ms = context_latency
        return True


class JsonLogFormatter(logging.Formatter):
    """Formatter that outputs structured JSON log lines."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        log_record: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "job_id": getattr(record, "job_id", None),
            "latency_ms": getattr(record, "latency_ms", None),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack"] = self.formatStack(record.stack_info)

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in LOG_RECORD_BUILTINS and not key.startswith("_")
        }
        if extra:
            log_record["extra"] = extra

        return json.dumps({k: v for k, v in log_record.items() if v is not None})


def bind_request_id(request_id: Optional[str]) -> Optional[Token]:
    """Bind a request identifier to the logging context."""

    if request_id is None:
        return _request_id_ctx.set(None)
    return _request_id_ctx.set(request_id)


def release_request_id(token: Optional[Token]) -> None:
    """Release a bound request identifier from the logging context."""

    if token is not None:
        _request_id_ctx.reset(token)
    else:  # pragma: no cover - defensive guard
        _request_id_ctx.set(None)


def get_request_id() -> Optional[str]:
    """Return the active request identifier, if any."""

    return _request_id_ctx.get()


def generate_request_id() -> str:
    """Generate a unique request identifier suitable for tracing."""

    return uuid4().hex


def bind_job_id(job_id: Optional[str]) -> Optional[Token]:
    """Bind a job identifier to the logging context."""

    return _job_id_ctx.set(job_id)


def release_job_id(token: Optional[Token]) -> None:
    """Release a bound job identifier from the logging context."""

    if token is not None:
        _job_id_ctx.reset(token)
    else:  # pragma: no cover - defensive guard
        _job_id_ctx.set(None)


def get_job_id() -> Optional[str]:
    """Return the active job identifier, if any."""

    return _job_id_ctx.get()


def bind_latency(latency_ms: Optional[float]) -> Optional[Token]:
    """Bind a latency measurement (in milliseconds) to the logging context."""

    return _latency_ctx.set(latency_ms)


def release_latency(token: Optional[Token]) -> None:
    """Release a bound latency measurement from the logging context."""

    if token is not None:
        _latency_ctx.reset(token)
    else:  # pragma: no cover - defensive guard
        _latency_ctx.set(None)


def get_latency() -> Optional[float]:
    """Return the active latency measurement, if any."""

    return _latency_ctx.get()


def get_system_logger(name: str = "whisper_api", level: Optional[str] = None) -> logging.Logger:
    """Get a configured system logger."""

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False

    formatter = JsonLogFormatter()
    redactor = EnvironmentSecretRedactor({key: os.getenv(key, "") for key in SENSITIVE_ENV_VARS})
    request_filter = RequestIdFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redactor)
    console_handler.addFilter(request_filter)
    logger.addHandler(console_handler)

    logs_dir = Path("logs")
    if logs_dir.exists():
        file_handler = logging.FileHandler(logs_dir / "api.log")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redactor)
        file_handler.addFilter(request_filter)
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


__all__ = [
    "get_system_logger",
    "get_backend_logger",
    "get_app_logger",
    "get_logger",
    "bind_request_id",
    "release_request_id",
    "get_request_id",
    "generate_request_id",
    "bind_job_id",
    "release_job_id",
    "get_job_id",
    "bind_latency",
    "release_latency",
    "get_latency",
]
