"""
Enhanced transcript management models for T033.
Extends existing models with advanced features like versioning, tagging, and search.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import DateTime, Enum, Integer, String, Text, Float, Boolean, Index, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.orm_bootstrap import Base


class TranscriptVersion(Base):
    """Track versions of transcript edits."""
    __tablename__ = "transcript_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # user who made the edit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Database indexes for performance
    __table_args__ = (
        Index('idx_transcript_versions_job_id', 'job_id'),
        Index('idx_transcript_versions_job_id_version', 'job_id', 'version_number'),
        Index('idx_transcript_versions_current', 'job_id', 'is_current'),
    )

    def __repr__(self):
        return f"<TranscriptVersion job_id={self.job_id} version={self.version_number}>"


class TranscriptTag(Base):
    """Custom tags for transcript organization."""
    __tablename__ = "transcript_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True, default="#3B82F6")  # hex color
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self):
        return f"<TranscriptTag name={self.name}>"


class JobTag(Base):
    """Many-to-many relationship between jobs and tags."""
    __tablename__ = "job_tags"

    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(Integer, ForeignKey("transcript_tags.id"), primary_key=True)
    assigned_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Database indexes for performance
    __table_args__ = (
        Index('idx_job_tags_job_id', 'job_id'),
        Index('idx_job_tags_tag_id', 'tag_id'),
    )


class TranscriptBookmark(Base):
    """Bookmarks for specific points in transcripts."""
    __tablename__ = "transcript_bookmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), nullable=False)
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)  # seconds in audio
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Database indexes for performance
    __table_args__ = (
        Index('idx_transcript_bookmarks_job_id', 'job_id'),
        Index('idx_transcript_bookmarks_timestamp', 'job_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<TranscriptBookmark job_id={self.job_id} timestamp={self.timestamp}>"


class TranscriptSearchIndex(Base):
    """Full-text search index for transcripts."""
    __tablename__ = "transcript_search_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String, ForeignKey("jobs.id"), nullable=False, unique=True)
    content_tokens: Mapped[str] = mapped_column(Text, nullable=False)  # preprocessed searchable content
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # extracted keywords
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Database indexes for performance
    __table_args__ = (
        Index('idx_transcript_search_job_id', 'job_id'),
    )


class BatchOperation(Base):
    """Track batch operations on multiple transcripts."""
    __tablename__ = "batch_operations"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)  # export, delete, tag, etc.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    job_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # list of job IDs
    parameters: Mapped[dict] = mapped_column(JSON, nullable=True)  # operation-specific parameters
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # operation results
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Database indexes for performance
    __table_args__ = (
        Index('idx_batch_operations_status', 'status'),
        Index('idx_batch_operations_type', 'operation_type'),
        Index('idx_batch_operations_created', 'created_at'),
    )

    def __repr__(self):
        return f"<BatchOperation id={self.id} type={self.operation_type} status={self.status}>"


class TranscriptExport(Base):
    """Track export operations and file locations."""
    __tablename__ = "transcript_exports"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # UUID
    job_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # can be single or multiple jobs
    export_format: Mapped[str] = mapped_column(String(10), nullable=False)  # srt, vtt, docx, pdf, json
    export_options: Mapped[dict] = mapped_column(JSON, nullable=True)  # format-specific options
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # path to generated file
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # auto-cleanup
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Database indexes for performance
    __table_args__ = (
        Index('idx_transcript_exports_format', 'export_format'),
        Index('idx_transcript_exports_created', 'created_at'),
        Index('idx_transcript_exports_expires', 'expires_at'),
    )

    def __repr__(self):
        return f"<TranscriptExport id={self.id} format={self.export_format}>"