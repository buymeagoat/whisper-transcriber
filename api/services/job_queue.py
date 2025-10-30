"""Celery-backed job queue utilities."""

from __future__ import annotations

from typing import Any, Optional

from celery import Celery
from celery.result import AsyncResult

from api.utils.logger import get_backend_logger
from api.worker import celery_app


LOGGER = get_backend_logger()


def _resolve_task_name(task_name: str) -> str:
    """Return a fully-qualified Celery task name."""

    if "." in task_name:
        return task_name
    return f"api.services.app_worker.{task_name}"


class CeleryJobQueue:
    """A thin wrapper around Celery for submitting and inspecting jobs."""

    def __init__(self, app: Celery | None = None) -> None:
        self._app = app or celery_app

    def submit_job(self, task_name: str, **kwargs: Any) -> str:
        """Submit ``task_name`` to Celery and return the task identifier."""

        qualified_name = _resolve_task_name(task_name)
        task = self._app.signature(qualified_name, kwargs=kwargs)
        task_id = kwargs.get("job_id")
        result = task.apply_async(task_id=task_id)
        LOGGER.info("Submitted Celery task %s as %s", qualified_name, result.id)
        return result.id

    def get_job(self, task_id: str) -> Optional[AsyncResult]:
        """Return the Celery ``AsyncResult`` for ``task_id`` if available."""

        if not task_id:
            return None
        return AsyncResult(task_id, app=self._app)

    def get_job_status(self, task_id: str) -> Optional[str]:
        """Return the Celery state for ``task_id``."""

        result = self.get_job(task_id)
        return result.state if result else None

    def cancel_job(self, task_id: str) -> bool:
        """Attempt to revoke a queued or running task."""

        result = self.get_job(task_id)
        if not result:
            return False

        result.revoke(terminate=True)
        LOGGER.info("Revoked Celery task %s", task_id)
        return True


# Global job queue instance used throughout the application.
job_queue = CeleryJobQueue()
