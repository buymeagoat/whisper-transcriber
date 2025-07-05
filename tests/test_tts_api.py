import importlib
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import models, orm_bootstrap, paths, app_state
from api.models import Job, JobStatusEnum
from api.routes import tts
from api.errors import ErrorCode


def create_tts_app(tmp_path):
    paths.UPLOAD_DIR = tmp_path / "uploads"
    paths.TRANSCRIPTS_DIR = tmp_path / "transcripts"
    paths.LOG_DIR = tmp_path / "logs"
    for p in (paths.UPLOAD_DIR, paths.TRANSCRIPTS_DIR, paths.LOG_DIR):
        p.mkdir(parents=True, exist_ok=True)

    app_state.UPLOAD_DIR = paths.UPLOAD_DIR
    app_state.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    app_state.LOG_DIR = paths.LOG_DIR

    importlib.reload(tts)
    tts.storage = paths.storage

    app = FastAPI()
    app.include_router(tts.router)
    return TestClient(app)


def test_generate_tts_init_failure(postgresql, tmp_path, monkeypatch):
    os.environ["DB_URL"] = postgresql.url()
    importlib.reload(orm_bootstrap)
    models.Base.metadata.create_all(orm_bootstrap.engine)

    client = create_tts_app(tmp_path)

    job_id = "jobtts"
    transcript_dir = paths.TRANSCRIPTS_DIR / job_id
    transcript_dir.mkdir(parents=True)
    transcript = transcript_dir / "out.srt"
    transcript.write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n")

    with orm_bootstrap.SessionLocal() as db:
        db.add(
            Job(
                id=job_id,
                original_filename="f.wav",
                saved_filename="f.wav",
                model="base",
                status=JobStatusEnum.COMPLETED,
                transcript_path=str(transcript),
            )
        )
        db.commit()

    def fail_init(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(tts.pyttsx3, "init", fail_init)

    resp = client.post(f"/tts/{job_id}")
    assert resp.status_code == 500
    assert resp.json()["code"] == ErrorCode.WHISPER_RUNTIME
