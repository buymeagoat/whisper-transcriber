import importlib
import pytest


@pytest.mark.asyncio
async def test_check_celery_connection_retries(monkeypatch):
    monkeypatch.setenv("JOB_QUEUE_BACKEND", "broker")
    import api.app_state as app_state

    importlib.reload(app_state)

    attempts = []

    def fake_ping(timeout=1):
        attempts.append("ping")
        if len(attempts) < 3:
            return []
        return ["pong"]

    async def fake_sleep(_):
        attempts.append("sleep")

    celery_app_module = importlib.import_module("api.services.celery_app")
    monkeypatch.setattr(celery_app_module.celery_app.control, "ping", fake_ping)
    monkeypatch.setattr(app_state.asyncio, "sleep", fake_sleep)

    await app_state.check_celery_connection()

    assert attempts.count("ping") == 3
