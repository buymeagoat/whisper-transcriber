import importlib
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import paths, app_state
from api.routes import admin, auth
from api.services.job_queue import ThreadJobQueue
from api.services.users import create_user
from api.orm_bootstrap import SessionLocal
from api.models import Job, JobStatusEnum


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


def test_admin_stats_returns_kpis(admin_client):
    create_user("admin", "pw", role="admin")
    start = datetime.utcnow()
    end = start + timedelta(seconds=2)
    with SessionLocal() as db:
        job = Job(
            id="job1",
            original_filename="x.wav",
            saved_filename="x.wav",
            model="base",
            status=JobStatusEnum.COMPLETED,
            started_at=start,
            finished_at=end,
        )
        db.add(job)
        db.commit()

    token = _token(admin_client, "admin", "pw")
    resp = admin_client.get(
        "/admin/stats", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["completed_jobs"] >= 1
    assert data["avg_job_time"] >= 0
    assert "queue_length" in data
