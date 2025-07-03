import importlib
import io
import shutil
from pathlib import Path

from api import app_state, paths, orm_bootstrap
from api.models import Job, JobStatusEnum
from api.services.storage import LocalStorage


def setup_storage(tmp_path):
    storage = LocalStorage(tmp_path)
    paths.storage = storage
    paths.UPLOAD_DIR = storage.upload_dir
    paths.TRANSCRIPTS_DIR = storage.transcripts_dir
    paths.LOG_DIR = storage.log_dir
    app_state.UPLOAD_DIR = paths.UPLOAD_DIR
    app_state.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    app_state.LOG_DIR = paths.LOG_DIR
    return storage


def test_transcript_dir_removed_on_metadata_failure(
    temp_db, tmp_path, sample_wav, monkeypatch
):
    storage = setup_storage(tmp_path)
    importlib.reload(app_state)
    app_state.UPLOAD_DIR = paths.UPLOAD_DIR
    app_state.TRANSCRIPTS_DIR = paths.TRANSCRIPTS_DIR
    app_state.LOG_DIR = paths.LOG_DIR

    monkeypatch.setattr(app_state, "get_duration", lambda x: 1.0)

    def fail_writer(*a, **k):
        raise RuntimeError("fail")

    monkeypatch.setattr(app_state, "run_metadata_writer", fail_writer)

    class DummyPopen:
        def __init__(self, cmd, stdout=None, stderr=None, text=True, bufsize=1):
            self.returncode = 0
            self.stdout = io.StringIO()
            self.stderr = io.StringIO()
            out_dir = Path(cmd[cmd.index("--output_dir") + 1])
            inp = Path(cmd[1])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / (inp.stem + ".srt")).write_text("x")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def wait(self):
            return 0

    monkeypatch.setattr(app_state, "Popen", DummyPopen)
    monkeypatch.setattr(app_state.shutil, "which", lambda x: "/bin/echo")

    job_id = "job1"
    upload_path = storage.upload_dir / "file.wav"
    shutil.copy(sample_wav, upload_path)
    job_dir = storage.transcripts_dir / job_id

    with orm_bootstrap.SessionLocal() as db:
        db.add(
            Job(
                id=job_id,
                original_filename="file.wav",
                saved_filename="file.wav",
                model="base",
                status=JobStatusEnum.QUEUED,
            )
        )
        db.commit()

    app_state.handle_whisper(job_id, upload_path, job_dir, "base", start_thread=False)

    assert not job_dir.exists()
    with orm_bootstrap.SessionLocal() as db:
        job = db.query(Job).get(job_id)
        assert job.status == JobStatusEnum.FAILED_UNKNOWN
