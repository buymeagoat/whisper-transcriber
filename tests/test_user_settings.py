import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import paths, app_state
from api.routes import user_settings, auth
from api.services.job_queue import ThreadJobQueue
from api.services.users import create_user
from api.services import user_settings as service


@pytest.fixture
def settings_client(temp_db, temp_dirs):
    importlib.reload(app_state)
    app_state.job_queue = ThreadJobQueue(1)
    app_state.handle_whisper = lambda *a, **k: None
    app_state.UPLOAD_DIR = paths.UPLOAD_DIR
    app_state.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    app_state.LOG_DIR = paths.LOG_DIR

    importlib.reload(user_settings)
    app = FastAPI()
    for router in (user_settings.router, auth.router):
        app.include_router(router)

    client = TestClient(app)
    yield client
    app_state.job_queue.shutdown()


def _token(client, username, password):
    return client.post(
        "/token", data={"username": username, "password": password}
    ).json()["access_token"]


def test_update_persists(settings_client):
    create_user("bob", "pw")
    token = _token(settings_client, "bob", "pw")

    resp = settings_client.post(
        "/user/settings",
        json={"default_model": "base"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["default_model"] == "base"

    resp = settings_client.get(
        "/user/settings", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["default_model"] == "base"

    values = service.get_settings(1)
    assert values.get("default_model") == "base"


def test_requires_auth(settings_client):
    resp = settings_client.get("/user/settings")
    assert resp.status_code == 401
    resp = settings_client.post("/user/settings", json={"default_model": "tiny"})
    assert resp.status_code == 401
