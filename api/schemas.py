from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from api.models import JobStatusEnum


class JobOut(BaseModel):
    """Representation of a single job."""

    id: str
    original_filename: str
    model: str
    created_at: datetime
    updated: datetime
    status: JobStatusEnum


class JobListOut(JobOut):
    """Representation used when listing jobs."""

    model_config = ConfigDict(from_attributes=True)


class MetadataOut(BaseModel):
    """Metadata information for a transcript."""

    tokens: int
    duration: int
    abstract: str
    sample_rate: Optional[int] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCreatedOut(BaseModel):
    """Response after creating a job."""

    job_id: str


class StatusOut(BaseModel):
    """Generic status message."""

    status: str
    message: Optional[str] = None


class FileListOut(BaseModel):
    logs: list[str]
    uploads: list[str]
    transcripts: list[str]


class BrowseOut(BaseModel):
    directories: list[str]
    files: list[str]


class AdminStatsOut(BaseModel):
    cpu_percent: float
    mem_used_mb: float
    mem_total_mb: float
    completed_jobs: int
    avg_job_time: float
    queue_length: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str


class CleanupConfigOut(BaseModel):
    cleanup_enabled: bool
    cleanup_days: int


class CleanupConfigIn(BaseModel):
    cleanup_enabled: Optional[bool] = None
    cleanup_days: Optional[int] = None


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListOut(BaseModel):
    users: list[UserOut]


class UserUpdateIn(BaseModel):
    role: str
