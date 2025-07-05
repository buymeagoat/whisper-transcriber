from pathlib import Path
import subprocess
import shutil

from api.errors import ErrorCode
import api.routes.audio as audio


def test_convert_success(client, sample_wav, monkeypatch, tmp_path):
    def fake_run(cmd, check, stdout=None, stderr=None):
        dest = Path(cmd[-1])
        shutil.copy(sample_wav, dest)
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/convert",
            data={"target_format": "mp3"},
            files={"file": ("in.wav", f, "audio/wav")},
        )
    assert resp.status_code == 200
    path = Path(resp.json()["path"])
    assert path.exists()
    assert path.suffix == ".mp3"


def test_convert_unsupported_format(client, sample_wav):
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/convert",
            data={"target_format": "xyz"},
            files={"file": ("in.wav", f, "audio/wav")},
        )
    assert resp.status_code == 415
    detail = resp.json()
    assert detail["code"] == ErrorCode.UNSUPPORTED_MEDIA


def test_edit_trim_volume(client, sample_wav, monkeypatch):
    def fake_run(cmd, check, stdout=None, stderr=None):
        dest = Path(cmd[-1])
        shutil.copy(sample_wav, dest)
        return subprocess.CompletedProcess(cmd, 0, b"", b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/edit",
            data={"trim_start": "0", "trim_end": "1", "volume": "1.5"},
            files={"file": ("clip.wav", f, "audio/wav")},
        )
    assert resp.status_code == 200
    path = Path(resp.json()["path"])
    assert path.exists()


def test_convert_ffmpeg_error_cleanup(client, sample_wav, monkeypatch):
    def fake_run(cmd, check, stdout=None, stderr=None):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    from api import paths

    with sample_wav.open("rb") as f:
        resp = client.post(
            "/convert",
            data={"target_format": "mp3"},
            files={"file": ("in.wav", f, "audio/wav")},
        )

    assert resp.status_code == 415
    assert resp.json()["code"] == ErrorCode.UNSUPPORTED_MEDIA
    assert not any(paths.UPLOAD_DIR.iterdir())


def test_edit_ffmpeg_error_cleanup(client, sample_wav, monkeypatch):
    def fake_run(cmd, check, stdout=None, stderr=None):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)
    from api import paths

    with sample_wav.open("rb") as f:
        resp = client.post(
            "/edit",
            data={"volume": "1"},
            files={"file": ("clip.wav", f, "audio/wav")},
        )

    assert resp.status_code == 415
    assert resp.json()["code"] == ErrorCode.UNSUPPORTED_MEDIA
    assert not any(paths.UPLOAD_DIR.iterdir())


def test_convert_save_error(client, sample_wav, monkeypatch):
    def fail_save(fileobj, name):
        raise OSError("disk error")

    monkeypatch.setattr(audio.storage, "save_upload", fail_save)
    with sample_wav.open("rb") as f:
        resp = client.post(
            "/convert",
            data={"target_format": "mp3"},
            files={"file": ("in.wav", f, "audio/wav")},
        )

    assert resp.status_code == 500
    assert resp.json()["code"] == ErrorCode.FILE_SAVE_FAILED
