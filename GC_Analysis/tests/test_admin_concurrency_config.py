import importlib
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import paths, app_state
from api.routes import admin, auth
from api.services.job_queue import ThreadJobQueue
from api.services.users import create_user


@pytest.fixture
def admin_client(temp_db, temp_dirs):
    importlib.reload(app_state)
    app_state.job_queue = ThreadJobQueue(1)
    app_state.handle_whisper = lambda *a, **k: None
    app_state.UPLOAD_DIR = paths.UPLOAD_DIR
    app_state.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    app_state.LOG_DIR = paths.LOG_DIR

    importlib.reload(admin)
    admin.storage = paths.storage
    admin.UPLOAD_DIR = paths.UPLOAD_DIR
    admin.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    admin.LOG_DIR = paths.LOG_DIR

    app = FastAPI()
    for router in (admin.router, auth.router):
        app.include_router(router)

    client = TestClient(app)
    yield client
    app_state.job_queue.shutdown()


def _token(client, username, password):
    return client.post(
        "/token", data={"username": username, "password": password}
    ).json()["access_token"]


def test_worker_resize_processes_jobs(admin_client):
    create_user("admin", "pw", role="admin")
    token = _token(admin_client, "admin", "pw")

    assert len(app_state.job_queue._threads) == 1

    resp = admin_client.post(
        "/admin/concurrency",
        json={"max_concurrent_jobs": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    for _ in range(50):
        if len(app_state.job_queue._threads) == 2:
            break
        time.sleep(0.01)
    assert len(app_state.job_queue._threads) == 2

    calls = []
    app_state.job_queue.enqueue(lambda: calls.append(1))
    app_state.job_queue.join()
    assert calls == [1]

    resp = admin_client.post(
        "/admin/concurrency",
        json={"max_concurrent_jobs": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    for _ in range(50):
        if len(app_state.job_queue._threads) == 1:
            break
        time.sleep(0.01)
    assert len(app_state.job_queue._threads) == 1
