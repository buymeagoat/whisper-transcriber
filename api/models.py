from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, Float, Boolean, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey


# ─── Base Class ─────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── Users Table ─────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


# ─── Enum Class ─────────────────────────────────────────────────────────
# These values are used in logs, API responses, and DB — use machine-safe slugs
class JobStatusEnum(str, PyEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    ENRICHING = "enriching"
    COMPLETED = "completed"
    FAILED = "failed"
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
        Enum(JobStatusEnum, values_callable=lambda e: [v.value for v in e]),
        nullable=False,
        default=JobStatusEnum.QUEUED,
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
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Job id={self.id} status={self.status.value}>"


# ─── MVP Metadata Table ─────────────────────────────────────────────────
class TranscriptMetadata(Base):
    __tablename__ = "metadata"

    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), primary_key=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lang: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    wpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sentiment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Metadata job_id={self.job_id} tokens={self.tokens} duration={self.duration}>"


# ─── Simple Config Table ─────────────────────────────────────────────────────
class ConfigEntry(Base):
    """Key/value storage for small configuration items."""

    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<Config {self.key}={self.value}>"


# ─── User Settings Table ─────────────────────────────────────────────────────
class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<UserSetting {self.user_id}:{self.key}={self.value}>"


# ─── Audit Logs Table ─────────────────────────────────────────────────────────
class AuditLog(Base):
    """Audit log database model for tracking security events and user actions"""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)  # Support IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    endpoint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string for additional data
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_time_type', 'timestamp', 'event_type'),
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_ip_time', 'client_ip', 'timestamp'),
        Index('idx_audit_severity_time', 'severity', 'timestamp'),
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<AuditLog {self.id}:{self.event_type}@{self.timestamp}>"
