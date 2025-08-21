import io
import tempfile
import pytest

from fastapi import HTTPException
from botocore.exceptions import BotoCoreError

from api.services.storage import CloudStorage
from api.errors import ErrorCode


class DummyS3:
    def upload_file(self, *a, **k):
        pass

    def download_file(self, *a, **k):
        pass

    def get_paginator(self, *a, **k):
        class P:
            def paginate(self, **kw):
                yield {"Contents": []}

        return P()

    def delete_object(self, *a, **k):
        pass


def test_save_upload_s3_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    storage = CloudStorage("bucket")
    storage.s3 = DummyS3()

    def fail(*a, **k):
        raise BotoCoreError()

    monkeypatch.setattr(storage.s3, "upload_file", fail)

    with pytest.raises(HTTPException) as exc:
        storage.save_upload(io.BytesIO(b"data"), "f.bin")
    assert exc.value.detail["code"] == ErrorCode.FILE_SAVE_FAILED


def test_get_upload_path_s3_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    storage = CloudStorage("bucket")
    storage.s3 = DummyS3()

    def fail(*a, **k):
        raise BotoCoreError()

    monkeypatch.setattr(storage.s3, "download_file", fail)

    with pytest.raises(HTTPException) as exc:
        storage.get_upload_path("f.bin")
    assert exc.value.detail["code"] == ErrorCode.CLOUD_STORAGE_ERROR


def test_delete_transcript_dir_s3_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    storage = CloudStorage("bucket")
    storage.s3 = DummyS3()

    def fail_get_paginator(*a, **k):
        raise BotoCoreError()

    monkeypatch.setattr(storage.s3, "get_paginator", fail_get_paginator)

    with pytest.raises(HTTPException) as exc:
        storage.delete_transcript_dir("job")
    assert exc.value.detail["code"] == ErrorCode.CLOUD_STORAGE_ERROR
