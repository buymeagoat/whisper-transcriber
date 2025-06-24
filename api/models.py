from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey


# ─── Base Class ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── Enum Class ─────────────────────────────────────────────────────────
# These values are used in logs, API responses, and DB — use machine-safe slugs
class JobStatusEnum(PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    ENRICHING = "enriching"
    COMPLETED = "completed"
    FAILED = "failed"
    STALLED = "stalled"
    FAILED_TIMEOUT = "failed_timeout"
    FAILED_LAUNCH_ERROR = "failed_launch_error"
    FAILED_WHISPER_ERROR = "failed_whisper_error"
    FAILED_THREAD_EXCEPTION = "failed_thread_exception"
    FAILED_UNKNOWN = "failed_unknown"


# ─── Jobs Table ─────────────────────────────────────────────────────────
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    saved_filename: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[JobStatusEnum] = mapped_column(
        Enum(JobStatusEnum), nullable=False, default=JobStatusEnum.QUEUED
    )
    # Filled after processing: should not be empty if status is COMPLETED
    transcript_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Path to job log file, created during whisper run or on failure
    log_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Job id={self.id} status={self.status.value}>"


# ─── MVP Metadata Table ─────────────────────────────────────────────────
class TranscriptMetadata(Base):
    __tablename__ = "metadata"

    __table_args__ = (
        # Enforces better SQLite compatibility and future-proofing
        {"sqlite_autoincrement": True},
    )

    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), primary_key=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Metadata job_id={self.job_id} tokens={self.tokens} duration={self.duration}>"
