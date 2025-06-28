import os
import importlib
import wave

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import models, orm_bootstrap, paths, app_state
from api.routes import jobs, auth, logs, metrics, progress, audio
from api.services.job_queue import ThreadJobQueue


@pytest.fixture
def temp_db(postgresql):
    os.environ["DB_URL"] = postgresql.url()
    import api.settings as settings

    importlib.reload(settings)
    importlib.reload(orm_bootstrap)
    models.Base.metadata.create_all(orm_bootstrap.engine)
    yield postgresql
    models.Base.metadata.drop_all(orm_bootstrap.engine)


@pytest.fixture
def temp_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))
    import api.settings as settings

    importlib.reload(settings)
    importlib.reload(paths)
    storage = paths.storage
    assert paths.UPLOAD_DIR.parent == tmp_path
    assert paths.TRANSCRIPTS_DIR.parent == tmp_path
    assert paths.LOG_DIR.parent == tmp_path
    return storage


@pytest.fixture
def client(temp_db, temp_dirs):
    importlib.reload(app_state)
    app_state.job_queue = ThreadJobQueue(1)
    app_state.handle_whisper = lambda *a, **k: None
    app_state.UPLOAD_DIR = paths.UPLOAD_DIR
    app_state.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    app_state.LOG_DIR = paths.LOG_DIR

    importlib.reload(jobs)
    jobs.SessionLocal = orm_bootstrap.SessionLocal
    jobs.UPLOAD_DIR = paths.UPLOAD_DIR
    jobs.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    jobs.LOG_DIR = paths.LOG_DIR
    jobs.handle_whisper = app_state.handle_whisper

    importlib.reload(audio)
    audio.UPLOAD_DIR = paths.UPLOAD_DIR
    audio.storage = paths.storage

    app = FastAPI()
    for router in (
        jobs.router,
        auth.router,
        logs.router,
        metrics.router,
        progress.router,
        audio.router,
    ):
        app.include_router(router)

    app.dependency_overrides[auth.get_current_user] = lambda: "testuser"
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    app_state.job_queue.shutdown()


@pytest.fixture
def sample_wav(tmp_path):
    path = tmp_path / "sample.wav"
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)
    return path
