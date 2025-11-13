"""
Database Performance Optimization Enhancement
Adds additional indexes and optimizations to improve query performance
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, Float, Boolean, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey


# ─── Enhanced Base Class with Performance Features ─────────────────────────────
class Base(DeclarativeBase):
    """Enhanced base class with performance tracking capabilities"""
    pass


# ─── Enhanced Users Table with Optimized Indexes ─────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="user")
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Enhanced database indexes for performance optimization
    __table_args__ = (
        # Existing indexes
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email', unique=True),
        Index('idx_users_role', 'role'),
        
        # New performance indexes
        Index('idx_users_active', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
        Index('idx_users_last_login', 'last_login'),
        Index('idx_users_role_active', 'role', 'is_active'),  # Composite for admin queries
        Index('idx_users_active_created', 'is_active', 'created_at'),  # For user listings
    )


# ─── Job Status Enum (unchanged) ─────────────────────────────────────────────────
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


# ─── Enhanced Jobs Table with Performance Optimizations ─────────────────────────
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
    # User association for multi-user support via external identity providers
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, default="legacy"
    )
    
    # Filled after processing
    transcript_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    log_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Enhanced timestamp fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Performance tracking fields
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Comprehensive database indexes for optimal performance
    __table_args__ = (
        # Existing indexes
        Index('idx_jobs_status', 'status'),
        Index('idx_jobs_created_at', 'created_at'),
        Index('idx_jobs_status_created', 'status', 'created_at'),
        Index('idx_jobs_model', 'model'),
        
        # Enhanced performance indexes
        Index('idx_jobs_user_id', 'user_id'),
        Index('idx_jobs_user_status', 'user_id', 'status'),
        Index('idx_jobs_user_created', 'user_id', 'created_at'),
        Index('idx_jobs_status_updated', 'status', 'updated_at'),
        Index('idx_jobs_finished_at', 'finished_at'),
        Index('idx_jobs_started_at', 'started_at'),
        
        # Composite indexes for common query patterns
        Index('idx_jobs_user_status_created', 'user_id', 'status', 'created_at'),  # User job listings
        Index('idx_jobs_status_model_created', 'status', 'model', 'created_at'),   # Model performance analysis
        Index('idx_jobs_created_status_model', 'created_at', 'status', 'model'),   # Time-based analysis
        
        # Performance analysis indexes
        Index('idx_jobs_processing_time', 'processing_time_seconds'),
        Index('idx_jobs_file_size', 'file_size_bytes'),
        Index('idx_jobs_duration', 'duration_seconds'),
    )

    def __repr__(self):
        return f"<Job id={self.id} status={self.status.value} user_id={self.user_id}>"


# ─── Enhanced Transcript Metadata with Performance Indexes ─────────────────────
class TranscriptMetadata(Base):
    __tablename__ = "metadata"

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

    # Enhanced indexes for metadata queries
    __table_args__ = (
        # Existing indexes
        Index('idx_metadata_job_id', 'job_id'),
        
        # New performance indexes
        Index('idx_metadata_language', 'language'),
        Index('idx_metadata_generated_at', 'generated_at'),
        Index('idx_metadata_duration', 'duration'),
        Index('idx_metadata_tokens', 'tokens'),
        Index('idx_metadata_wpm', 'wpm'),
        Index('idx_metadata_sentiment', 'sentiment'),
        
        # Composite indexes for analytics
        Index('idx_metadata_lang_duration', 'language', 'duration'),
        Index('idx_metadata_lang_tokens', 'language', 'tokens'),
        Index('idx_metadata_generated_lang', 'generated_at', 'language'),
    )

    def __repr__(self):
        return f"<Metadata job_id={self.job_id} tokens={self.tokens} language={self.language}>"


# ─── Config Table (unchanged but with index) ─────────────────────────────────────
class ConfigEntry(Base):
    """Key/value storage for small configuration items."""
    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Performance index for config lookups
    __table_args__ = (
        Index('idx_config_updated_at', 'updated_at'),
    )

    def __repr__(self) -> str:
        return f"<Config {self.key}={self.value}>"


# ─── Enhanced User Settings with Performance Indexes ─────────────────────────────
class UserSetting(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Performance indexes for user settings
    __table_args__ = (
        Index('idx_user_settings_user_id', 'user_id'),
        Index('idx_user_settings_key', 'key'),
        Index('idx_user_settings_updated', 'updated_at'),
        Index('idx_user_settings_user_key', 'user_id', 'key'),  # Composite for lookups
    )

    def __repr__(self) -> str:
        return f"<UserSetting {self.user_id}:{self.key}={self.value}>"


# ─── Enhanced Audit Logs with Performance Optimizations ─────────────────────────
class AuditLog(Base):
    """Enhanced audit log model with performance optimizations"""
    
    __tablename__ = "audit_logs_optimized"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    endpoint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Enhanced composite indexes for audit log analysis
    __table_args__ = (
        # Existing indexes
        Index('idx_audit_time_type', 'timestamp', 'event_type'),
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_ip_time_opt', 'client_ip', 'timestamp'),
        Index('idx_audit_severity_time', 'severity', 'timestamp'),
        
        # New performance indexes
        Index('idx_audit_endpoint_time', 'endpoint', 'timestamp'),
        Index('idx_audit_status_time', 'status_code', 'timestamp'),
        Index('idx_audit_method_time', 'method', 'timestamp'),
        Index('idx_audit_resource_time', 'resource_type', 'timestamp'),
        Index('idx_audit_session_time', 'session_id', 'timestamp'),
        
        # Composite indexes for security analysis
        Index('idx_audit_ip_event_time', 'client_ip', 'event_type', 'timestamp'),
        Index('idx_audit_user_event_time', 'user_id', 'event_type', 'timestamp'),
        Index('idx_audit_severity_event_time', 'severity', 'event_type', 'timestamp'),
        Index('idx_audit_endpoint_method_time', 'endpoint', 'method', 'timestamp'),
        
        # Performance analysis indexes
        Index('idx_audit_time_status_endpoint', 'timestamp', 'status_code', 'endpoint'),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.id}:{self.event_type}@{self.timestamp} user={self.user_id}>"


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
