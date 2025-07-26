import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import paths, app_state
from api.routes import admin, auth
from api.services.job_queue import ThreadJobQueue
from api.services.users import create_user
from api.services import config as config_service


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


def test_admin_update_concurrency_persists(admin_client):
    create_user("admin", "pw", role="admin")
    token = _token(admin_client, "admin", "pw")

    resp = admin_client.post(
        "/admin/concurrency",
        json={"max_concurrent_jobs": 4},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"max_concurrent_jobs": 4}

    value = config_service.get_concurrency(2)
    assert value == 4


def test_concurrency_update_forbidden(admin_client):
    create_user("bob", "pw", role="user")
    token = _token(admin_client, "bob", "pw")

    resp = admin_client.post(
        "/admin/concurrency",
        json={"max_concurrent_jobs": 4},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_admin_update_concurrency_invalid(admin_client):
    create_user("admin", "pw", role="admin")
    token = _token(admin_client, "admin", "pw")

    resp = admin_client.post(
        "/admin/concurrency",
        json={"max_concurrent_jobs": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
