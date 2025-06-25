from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import shutil


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
    """Placeholder for a cloud backed storage implementation."""

    def __init__(self) -> None:
        pass

    @property
    def upload_dir(self) -> Path:
        raise NotImplementedError

    @property
    def transcripts_dir(self) -> Path:
        raise NotImplementedError

    @property
    def log_dir(self) -> Path:
        raise NotImplementedError

    def save_upload(self, source: BinaryIO, filename: str) -> Path:
        raise NotImplementedError

    def delete_upload(self, filename: str) -> None:
        raise NotImplementedError

    def get_upload_path(self, filename: str) -> Path:
        raise NotImplementedError

    def get_transcript_dir(self, job_id: str) -> Path:
        raise NotImplementedError

    def delete_transcript_dir(self, job_id: str) -> None:
        raise NotImplementedError
