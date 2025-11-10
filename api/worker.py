"""Celery worker for background transcription processing."""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from celery import Celery
from redis import Redis

# Ensure we can import from api package
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.core.settings import get_core_settings

LOGGER = logging.getLogger("whisper.worker")
logging.basicConfig(
    level=os.getenv("WORKER_LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

settings = get_core_settings()


def _redis_connection_kwargs(redis_url: str) -> dict:
    """Parse a Redis URL into keyword arguments for redis-py."""
    parsed = urlparse(redis_url)
    if parsed.scheme not in {"redis", "rediss"}:
        raise ValueError(f"Unsupported Redis scheme: {parsed.scheme}")

    db = int(parsed.path.lstrip("/") or 0)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 6379,
        "db": db,
        "username": parsed.username,
        "password": parsed.password,
        "ssl": parsed.scheme == "rediss",
        "socket_connect_timeout": float(os.getenv("WORKER_REDIS_CONNECT_TIMEOUT", "5")),
    }


def ensure_redis_ready(redis_url: str, *, max_attempts: int = None) -> None:
    """Attempt to connect to Redis until it responds or retries are exhausted."""

    attempts = max_attempts or int(os.getenv("WORKER_REDIS_MAX_ATTEMPTS", "10"))
    base_delay = float(os.getenv("WORKER_REDIS_RETRY_DELAY", "1"))
    max_delay = float(os.getenv("WORKER_REDIS_MAX_DELAY", "5"))

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            client = Redis(**_redis_connection_kwargs(redis_url))
            client.ping()
            client.close()
            LOGGER.info("Redis broker at %s is ready (attempt %d)", redis_url, attempt)
            return
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc
            sleep_for = min(base_delay * (2 ** (attempt - 1)), max_delay)
            LOGGER.warning(
                "Redis not ready (attempt %d/%d): %s. Retrying in %.1fs",
                attempt,
                attempts,
                exc,
                sleep_for,
            )
            time.sleep(sleep_for)

    raise RuntimeError(f"Failed to connect to Redis after {attempts} attempts") from last_error


celery_app = Celery(
    "whisper_transcriber",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    result_backend=settings.celery_result_backend,
)

celery_app.autodiscover_tasks(["api.services"])

# Import task modules explicitly so health checks succeed without relying on
# Celery's default "tasks" module discovery naming.
import api.services.app_worker  # noqa: E402,F401


@celery_app.task(name="api.worker.health_check")
def worker_health_check() -> dict[str, str]:
    """Simple task to verify the worker is responsive."""

    return {"status": "ok"}


def bootstrap_worker() -> None:
    """Entrypoint used when running the worker module directly."""

    ensure_redis_ready(settings.celery_broker_url)
    concurrency = os.getenv("WORKER_CONCURRENCY")
    argv = [
        "worker",
        "--loglevel",
        os.getenv("WORKER_LOG_LEVEL", "info"),
    ]
    if concurrency:
        argv.extend(["--concurrency", concurrency])
    celery_app.worker_main(argv)


if __name__ == "__main__":  # pragma: no cover - manual execution path
    bootstrap_worker()
