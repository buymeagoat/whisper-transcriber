"""Entry point for launching the Celery worker."""

from api.services.celery_app import celery_app
from api.utils.logger import get_system_logger
import sys

log = get_system_logger()

if __name__ == "__main__":
    try:
        celery_app.worker_main()
    except Exception:  # pragma: no cover - defensive
        log.exception("Celery worker failed to start")
        sys.exit(1)
