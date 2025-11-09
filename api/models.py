from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, Float, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from api.orm_bootstrap import Base

# Import security audit models to ensure they're registered
from api.security.audit_models import SecurityAuditLog, APIKeyAudit, SecurityIncident


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

    # Add database indexes for performance
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_role', 'role'),
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
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, default="legacy"
    )
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

    # Add database indexes for performance
    __table_args__ = (
        Index('idx_jobs_status', 'status'),
        Index('idx_jobs_created_at', 'created_at'),
        Index('idx_jobs_status_created', 'status', 'created_at'),
        Index('idx_jobs_model', 'model'),
        Index('idx_jobs_user_status', 'user_id', 'status'),
    )

    def __repr__(self):
        return f"<Job id={self.id} status={self.status.value} user_id={self.user_id}>"


# ─── MVP Metadata Table ─────────────────────────────────────────────────
class TranscriptMetadata(Base):
    __tablename__ = "transcript_metadata"

    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), primary_key=True)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sentiment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Add database indexes for performance
    __table_args__ = (
        Index('idx_metadata_job_id', 'job_id'),
    )

    def __repr__(self):
        return f"<Metadata job_id={self.job_id} tokens={self.tokens} duration={self.duration}>"


# ─── Simple Config Table ─────────────────────────────────────────────────────
class ConfigEntry(Base):
    """Key/value storage for small configuration items."""

    __tablename__ = "config_entries"

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
    
    # Add composite indexes for common queries (with unique names to avoid conflicts)
    __table_args__ = (
        Index('idx_audit_log_time_type', 'timestamp', 'event_type'),
        Index('idx_audit_log_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_log_ip_time', 'client_ip', 'timestamp'),
        Index('idx_audit_log_severity_time', 'severity', 'timestamp'),
    )

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<AuditLog {self.id}:{self.event_type}@{self.timestamp}>"


# ─── Performance Metrics Table for Database Monitoring ─────────────────────────
class PerformanceMetric(Base):
    """Track database and application performance metrics"""
    
    __tablename__ = "performance_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # JSON string
    
    # Performance monitoring indexes
    __table_args__ = (
        Index('idx_perf_type_name', 'metric_type', 'metric_name'),
        Index('idx_perf_time_type', 'timestamp', 'metric_type'),
        Index('idx_perf_name_time', 'metric_name', 'timestamp'),
        Index('idx_perf_value', 'value'),
        Index('idx_perf_type_name_time', 'metric_type', 'metric_name', 'timestamp'),
    )

    def __repr__(self) -> str:
        return f"<PerformanceMetric {self.metric_type}:{self.metric_name}={self.value}>"


# ─── Query Performance Log for Slow Query Analysis ─────────────────────────────
class QueryPerformanceLog(Base):
    """Log slow database queries for performance analysis"""
    
    __tablename__ = "query_performance_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    query_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    table_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    endpoint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Slow query analysis indexes
    __table_args__ = (
        Index('idx_query_perf_time_duration', 'timestamp', 'execution_time_ms'),
        Index('idx_query_perf_type_duration', 'query_type', 'execution_time_ms'),
        Index('idx_query_perf_table_duration', 'table_name', 'execution_time_ms'),
        Index('idx_query_perf_endpoint_duration', 'endpoint', 'execution_time_ms'),
        Index('idx_query_perf_user_duration', 'user_id', 'execution_time_ms'),
        Index('idx_query_perf_slow_queries', 'execution_time_ms'),  # For finding slow queries
    )

    def __repr__(self) -> str:
        return f"<QueryPerformanceLog {self.query_type}:{self.execution_time_ms}ms>"
