"""Smoke tests for Celery integration."""

from api.core.settings import get_core_settings
from api.worker import celery_app, worker_health_check


def test_celery_routes_tasks_via_redis():
    """Ensure Celery is configured for Redis and can execute a basic task."""

    core_settings = get_core_settings()
    assert core_settings.broker_url().startswith(("redis://", "rediss://"))
    assert core_settings.result_backend().startswith(("redis://", "rediss://"))
    assert celery_app.conf.broker_url == core_settings.broker_url()
    assert celery_app.conf.result_backend == core_settings.result_backend()

    previous_always_eager = celery_app.conf.task_always_eager
    previous_store = celery_app.conf.task_store_eager_result
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = True
    try:
        result = worker_health_check.delay()
        payload = result.get(timeout=5)
    finally:
        celery_app.conf.task_always_eager = previous_always_eager
        celery_app.conf.task_store_eager_result = previous_store

    assert payload == {"status": "ok"}
