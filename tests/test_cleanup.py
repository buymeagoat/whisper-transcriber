import os
import time

from api import paths, app_state
from api.services.storage import LocalStorage
from api.settings import settings


def setup_storage(tmp_path):
    storage = LocalStorage(tmp_path)
    paths.storage = storage
    paths.UPLOAD_DIR = storage.upload_dir
    paths.TRANSCRIPTS_DIR = storage.transcripts_dir
    paths.LOG_DIR = storage.log_dir
    app_state.storage = storage
    app_state.UPLOAD_DIR = storage.upload_dir
    app_state.TRANSCRIPTS_DIR = storage.transcripts_dir
    app_state.LOG_DIR = storage.log_dir
    return storage


def test_cleanup_removes_old_files(tmp_path, monkeypatch):
    storage = setup_storage(tmp_path)
    monkeypatch.setattr(settings, "cleanup_enabled", True)
    monkeypatch.setattr(settings, "cleanup_days", 1)

    old_time = time.time() - 2 * 86400

    old_upload = storage.upload_dir / "old.txt"
    old_upload.write_text("x")
    os.utime(old_upload, (old_time, old_time))

    new_upload = storage.upload_dir / "new.txt"
    new_upload.write_text("y")

    old_transcript = storage.transcripts_dir / "oldjob"
    old_transcript.mkdir()
    (old_transcript / "out.srt").write_text("x")
    os.utime(old_transcript, (old_time, old_time))

    new_transcript = storage.transcripts_dir / "newjob"
    new_transcript.mkdir()
    (new_transcript / "out.srt").write_text("y")

    old_log = storage.log_dir / "old.log"
    old_log.write_text("x")
    os.utime(old_log, (old_time, old_time))

    new_log = storage.log_dir / "new.log"
    new_log.write_text("y")

    app_state.cleanup_once()

    assert not old_upload.exists()
    assert new_upload.exists()
    assert not old_transcript.exists()
    assert new_transcript.exists()
    assert not old_log.exists()
    assert new_log.exists()


def test_cleanup_respects_disabled_flag(tmp_path, monkeypatch):
    storage = setup_storage(tmp_path)
    monkeypatch.setattr(settings, "cleanup_enabled", False)
    monkeypatch.setattr(settings, "cleanup_days", 1)

    old_time = time.time() - 2 * 86400
    old_upload = storage.upload_dir / "old.txt"
    old_upload.write_text("x")
    os.utime(old_upload, (old_time, old_time))

    app_state.cleanup_once()

    assert old_upload.exists()
