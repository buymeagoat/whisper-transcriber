import os
import importlib
from fastapi.testclient import TestClient

from api import models, orm_bootstrap


def create_test_app(postgresql, tmp_path):
    os.environ["DB_URL"] = postgresql.url()
    os.environ.setdefault("SECRET_KEY", "test-secret")
    import api.settings as settings

    importlib.reload(settings)
    importlib.reload(orm_bootstrap)
    models.Base.metadata.create_all(orm_bootstrap.engine)

    from api import app_state
    from api import paths

    paths.UPLOAD_DIR = tmp_path / "uploads"
    paths.TRANSCRIPTS_DIR = tmp_path / "transcripts"
    paths.LOG_DIR = tmp_path / "logs"
    for p in (paths.UPLOAD_DIR, paths.TRANSCRIPTS_DIR, paths.LOG_DIR):
        p.mkdir(parents=True, exist_ok=True)

    app_state.UPLOAD_DIR = paths.UPLOAD_DIR
    app_state.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    app_state.LOG_DIR = paths.LOG_DIR

    app_state.handle_whisper = lambda *a, **k: None

    from api.routes import jobs

    importlib.reload(jobs)

    jobs.SessionLocal = orm_bootstrap.SessionLocal
    jobs.UPLOAD_DIR = paths.UPLOAD_DIR
    jobs.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    jobs.LOG_DIR = paths.LOG_DIR
    jobs.handle_whisper = app_state.handle_whisper

    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(jobs.router)
    return app


def test_submit_and_fetch_job(postgresql, tmp_path, sample_wav):
    app = create_test_app(postgresql, tmp_path)
    client = TestClient(app)

    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "base"},
            files={"file": ("test.wav", f, "audio/wav")},
        )

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    resp = client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == job_id
    assert data["original_filename"] == "test.wav"
    assert data["model"] == "base"
    assert data["status"] == "queued"


def test_submit_invalid_model(postgresql, tmp_path, sample_wav):
    app = create_test_app(postgresql, tmp_path)
    client = TestClient(app)

    with sample_wav.open("rb") as f:
        resp = client.post(
            "/jobs",
            data={"model": "bogus"},
            files={"file": ("test.wav", f, "audio/wav")},
        )

    assert resp.status_code == 400
