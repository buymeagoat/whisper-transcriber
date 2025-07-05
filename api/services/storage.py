from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import shutil
import tempfile
import boto3

from api.errors import ErrorCode, http_error
from api.settings import settings


class Storage(ABC):
    """Abstract storage backend for uploads and transcripts."""

    @property
    @abstractmethod
    def upload_dir(self) -> Path: ...

    @property
    @abstractmethod
    def transcripts_dir(self) -> Path: ...

    @property
    @abstractmethod
    def log_dir(self) -> Path: ...

    @abstractmethod
    def save_upload(self, source: BinaryIO, filename: str) -> Path: ...

    @abstractmethod
    def delete_upload(self, filename: str) -> None: ...

    @abstractmethod
    def get_upload_path(self, filename: str) -> Path: ...

    @abstractmethod
    def get_transcript_dir(self, job_id: str) -> Path: ...

    @abstractmethod
    def delete_transcript_dir(self, job_id: str) -> None: ...


class LocalStorage(Storage):
    """Filesystem based storage backend."""

    def __init__(self, base_dir: Path) -> None:
        self._upload_dir = base_dir / "uploads"
        self._transcripts_dir = base_dir / "transcripts"
        self._log_dir = base_dir / "logs"
        for path in (self._upload_dir, self._transcripts_dir, self._log_dir):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def upload_dir(self) -> Path:
        return self._upload_dir

    @property
    def transcripts_dir(self) -> Path:
        return self._transcripts_dir

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    def save_upload(self, source: BinaryIO, filename: str) -> Path:
        dest = self._upload_dir / filename
        with dest.open("wb") as dst:
            shutil.copyfileobj(source, dst)
        if dest.stat().st_size > settings.max_upload_size:
            dest.unlink(missing_ok=True)
            raise http_error(ErrorCode.FILE_TOO_LARGE)
        return dest

    def delete_upload(self, filename: str) -> None:
        try:
            (self._upload_dir / filename).unlink()
        except FileNotFoundError:
            pass

    def get_upload_path(self, filename: str) -> Path:
        return self._upload_dir / filename

    def get_transcript_dir(self, job_id: str) -> Path:
        path = self._transcripts_dir / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def delete_transcript_dir(self, job_id: str) -> None:
        shutil.rmtree(self._transcripts_dir / job_id, ignore_errors=True)


class CloudStorage(Storage):
    """S3 backed storage using boto3 with a local cache directory."""

    def __init__(
        self,
        bucket: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        session = boto3.session.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.s3 = session.client("s3")
        self.bucket = bucket
        base = Path(tempfile.gettempdir()) / "whisper_cache"
        self._upload_dir = base / "uploads"
        self._transcripts_dir = base / "transcripts"
        self._log_dir = base / "logs"
        for path in (self._upload_dir, self._transcripts_dir, self._log_dir):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def upload_dir(self) -> Path:
        return self._upload_dir

    @property
    def transcripts_dir(self) -> Path:
        return self._transcripts_dir

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    def save_upload(self, source: BinaryIO, filename: str) -> Path:
        dest = self._upload_dir / filename
        with dest.open("wb") as dst:
            shutil.copyfileobj(source, dst)
        if dest.stat().st_size > settings.max_upload_size:
            dest.unlink(missing_ok=True)
            raise http_error(ErrorCode.FILE_TOO_LARGE)
        self.s3.upload_file(str(dest), self.bucket, f"uploads/{filename}")
        return dest

    def delete_upload(self, filename: str) -> None:
        try:
            (self._upload_dir / filename).unlink()
        except FileNotFoundError:
            pass
        self.s3.delete_object(Bucket=self.bucket, Key=f"uploads/{filename}")

    def get_upload_path(self, filename: str) -> Path:
        path = self._upload_dir / filename
        if not path.exists():
            self.s3.download_file(self.bucket, f"uploads/{filename}", str(path))
        return path

    def get_transcript_dir(self, job_id: str) -> Path:
        path = self._transcripts_dir / job_id
        path.mkdir(parents=True, exist_ok=True)
        prefix = f"transcripts/{job_id}/"
        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                rel = key[len(prefix) :]
                local = path / rel
                local.parent.mkdir(parents=True, exist_ok=True)
                self.s3.download_file(self.bucket, key, str(local))
        return path

    def delete_transcript_dir(self, job_id: str) -> None:
        shutil.rmtree(self._transcripts_dir / job_id, ignore_errors=True)
        paginator = self.s3.get_paginator("list_objects_v2")
        prefix = f"transcripts/{job_id}/"
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                self.s3.delete_object(Bucket=self.bucket, Key=obj["Key"])
