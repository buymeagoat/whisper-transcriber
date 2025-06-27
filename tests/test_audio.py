from pathlib import Path
import subprocess
import shutil

from api.errors import ErrorCode


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
