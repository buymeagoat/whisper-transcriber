import importlib
import pytest
from fastapi import FastAPI

import api.main as main
from api.services.job_queue import ThreadJobQueue


@pytest.mark.asyncio
async def test_lifespan_shuts_down_queue(monkeypatch):
    importlib.reload(main)

    main.app_state.job_queue = ThreadJobQueue(1)
    called = False

    def fake_shutdown():
        nonlocal called
        called = True

    monkeypatch.setattr(main.app_state.job_queue, "shutdown", fake_shutdown)

    monkeypatch.setattr(main, "validate_or_initialize_database", lambda: None)
    monkeypatch.setattr(main, "ensure_default_admin", lambda *a, **k: None)
    monkeypatch.setattr(main, "validate_models_dir", lambda: None)

    async def _noop(*a, **k):
        pass

    monkeypatch.setattr(main, "check_celery_connection", _noop)
    monkeypatch.setattr(main, "rehydrate_incomplete_jobs", lambda: None)
    monkeypatch.setattr(main, "start_cleanup_thread", lambda: None)
    monkeypatch.setattr(main.settings, "cleanup_enabled", False)

    async with main.lifespan(FastAPI()):
        pass

    assert called
