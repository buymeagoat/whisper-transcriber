import io
import pytest
import tempfile

from api.services.storage import LocalStorage, CloudStorage
from api.errors import ErrorCode
from api.settings import settings
from fastapi import HTTPException


def test_save_upload_enforces_size_limit(tmp_path, monkeypatch):
    storage = LocalStorage(tmp_path)
    monkeypatch.setattr(settings, "max_upload_size", 10)
    data = io.BytesIO(b"x" * 11)
    with pytest.raises(HTTPException) as exc:
        storage.save_upload(data, "big.bin")
    assert exc.value.detail["code"] == ErrorCode.FILE_TOO_LARGE
    assert not (storage.upload_dir / "big.bin").exists()


class DummyS3:
    def upload_file(self, *a, **k):
        pass


def test_cloud_save_upload_enforces_size_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    storage = CloudStorage("bucket")
    storage.s3 = DummyS3()
    monkeypatch.setattr(settings, "max_upload_size", 10)
    data = io.BytesIO(b"x" * 11)
    with pytest.raises(HTTPException) as exc:
        storage.save_upload(data, "big.bin")
    assert exc.value.status_code == 413
    assert exc.value.detail["code"] == ErrorCode.FILE_TOO_LARGE
    assert not (storage.upload_dir / "big.bin").exists()
