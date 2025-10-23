"""
Database models for T034 Multi-Format Export System.
Provides comprehensive export functionality with templates, formats, and batch operations.
"""

from datetime import datetime, timedelta
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..orm_bootstrap import Base

class ExportFormat(PyEnum):
    """Supported export formats."""
    SRT = "srt"
    VTT = "vtt"
    DOCX = "docx"
    PDF = "pdf"
    JSON = "json"
    TXT = "txt"

class TemplateType(PyEnum):
    """Template types for different export formats."""
    SUBTITLE = "subtitle"  # For SRT/VTT
    DOCUMENT = "document"  # For DOCX/PDF
    STRUCTURED = "structured"  # For JSON
    PLAIN_TEXT = "plain_text"  # For TXT

class ExportStatus(PyEnum):
    """Export job status tracking."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchExportStatus(PyEnum):
    """Batch export status tracking."""
    CREATED = "created"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Some exports failed
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportTemplate(Base):
    """
    Export templates for customizable output formatting.
    Supports different template types with customizable styling and layout options.
    """
    __tablename__ = "export_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    template_type = Column(String(50), nullable=False, index=True)  # TemplateType enum
    supported_formats = Column(JSON, nullable=False)  # List of ExportFormat values
    
    # Template configuration
    template_config = Column(JSON, nullable=False)  # Format-specific configuration
    styling_config = Column(JSON)  # CSS/styling options for PDF/DOCX
    layout_config = Column(JSON)  # Layout options (margins, fonts, etc.)
    
    # Metadata
    created_by = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_system_template = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    exports = relationship("ExportJob", back_populates="template")
    
    def __repr__(self):
        return f"<ExportTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"


class ExportJob(Base):
    """
    Individual export jobs with format-specific processing.
    Tracks single transcript exports with detailed progress and metadata.
    """
    __tablename__ = "export_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), ForeignKey("jobs.id"), nullable=False, index=True)
    batch_export_id = Column(Integer, ForeignKey("batch_exports.id"), nullable=True, index=True)
    
    # Export configuration
    format = Column(String(20), nullable=False, index=True)  # ExportFormat enum
    template_id = Column(Integer, ForeignKey("export_templates.id"), nullable=True)
    custom_config = Column(JSON)  # Custom export settings
    
    # Processing details
    status = Column(String(20), default=ExportStatus.PENDING.value, nullable=False, index=True)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # Output information
    output_filename = Column(String(500), nullable=True)
    output_path = Column(String(1000), nullable=True)
    output_size_bytes = Column(Integer, nullable=True)
    output_url = Column(String(1000), nullable=True)  # For downloads
    
    # Processing metadata
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_duration_seconds = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Metadata
    created_by = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Auto-cleanup
    
    # Relationships
    job = relationship("Job", backref="export_jobs")
    batch_export = relationship("BatchExport", back_populates="export_jobs")
    template = relationship("ExportTemplate", back_populates="exports")
    
    def __repr__(self):
        return f"<ExportJob(id={self.id}, format='{self.format}', status='{self.status}')>"
    
    @property
    def is_expired(self):
        """Check if export has expired and should be cleaned up."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def calculate_duration(self):
        """Calculate processing duration in seconds."""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            self.processing_duration_seconds = delta.total_seconds()
            return self.processing_duration_seconds
        return None


class BatchExport(Base):
    """
    Batch export operations for multiple transcripts.
    Manages bulk export operations with progress tracking and queue management.
    """
    __tablename__ = "batch_exports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Batch configuration
    export_format = Column(String(20), nullable=False, index=True)  # ExportFormat enum
    template_id = Column(Integer, ForeignKey("export_templates.id"), nullable=True)
    batch_config = Column(JSON)  # Batch-specific settings
    
    # Job selection criteria
    job_ids = Column(JSON, nullable=False)  # List of job IDs to export
    filter_criteria = Column(JSON, nullable=True)  # Optional job filtering
    
    # Progress tracking
    status = Column(String(20), default=BatchExportStatus.CREATED.value, nullable=False, index=True)
    total_jobs = Column(Integer, nullable=False)
    completed_jobs = Column(Integer, default=0, nullable=False)
    failed_jobs = Column(Integer, default=0, nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    
    # Output management
    archive_filename = Column(String(500), nullable=True)  # ZIP archive name
    archive_path = Column(String(1000), nullable=True)
    archive_size_bytes = Column(Integer, nullable=True)
    download_url = Column(String(1000), nullable=True)
    
    # Processing metadata
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_duration_seconds = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    partial_success = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_by = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Auto-cleanup
    
    # Relationships
    export_jobs = relationship("ExportJob", back_populates="batch_export", cascade="all, delete-orphan")
    template = relationship("ExportTemplate")
    
    def __repr__(self):
        return f"<BatchExport(id={self.id}, name='{self.name}', format='{self.export_format}')>"
    
    def update_progress(self):
        """Update batch progress based on individual export jobs."""
        if self.total_jobs > 0:
            self.progress_percentage = (self.completed_jobs / self.total_jobs) * 100
        else:
            self.progress_percentage = 0.0
    
    def is_complete(self):
        """Check if batch export is complete."""
        return self.status in [BatchExportStatus.COMPLETED.value, BatchExportStatus.PARTIAL.value]
    
    def calculate_duration(self):
        """Calculate batch processing duration."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.processing_duration_seconds = delta.total_seconds()
            return self.processing_duration_seconds
        return None


class ExportHistory(Base):
    """
    Export history tracking for analytics and audit purposes.
    Maintains records of all export operations for reporting and analysis.
    """
    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True, index=True)
    export_job_id = Column(Integer, ForeignKey("export_jobs.id"), nullable=True, index=True)
    batch_export_id = Column(Integer, ForeignKey("batch_exports.id"), nullable=True, index=True)
    
    # Export details
    export_type = Column(String(20), nullable=False, index=True)  # 'single' or 'batch'
    format = Column(String(20), nullable=False, index=True)
    template_name = Column(String(255), nullable=True)
    
    # User information
    user_id = Column(String(255), nullable=True, index=True)
    user_email = Column(String(255), nullable=True, index=True)
    
    # Performance metrics
    processing_time_seconds = Column(Float, nullable=True)
    output_size_bytes = Column(Integer, nullable=True)
    job_count = Column(Integer, default=1, nullable=False)  # 1 for single, N for batch
    
    # Status tracking
    success = Column(Boolean, nullable=False, index=True)
    error_type = Column(String(100), nullable=True, index=True)
    error_details = Column(Text, nullable=True)
    
    # Timestamps
    exported_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    downloaded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    export_job = relationship("ExportJob")
    batch_export = relationship("BatchExport")
    
    def __repr__(self):
        return f"<ExportHistory(id={self.id}, type='{self.export_type}', format='{self.format}')>"


class ExportFormatConfig(Base):
    """
    System-wide export format configurations.
    Defines default settings and capabilities for each export format.
    """
    __tablename__ = "export_format_configs"

    id = Column(Integer, primary_key=True, index=True)
    format = Column(String(20), nullable=False, unique=True, index=True)  # ExportFormat enum
    
    # Format capabilities
    display_name = Column(String(100), nullable=False)
    file_extension = Column(String(10), nullable=False)
    mime_type = Column(String(100), nullable=False)
    supports_timestamps = Column(Boolean, default=False, nullable=False)
    supports_styling = Column(Boolean, default=False, nullable=False)
    supports_metadata = Column(Boolean, default=False, nullable=False)
    
    # Default configuration
    default_config = Column(JSON, nullable=False)
    validation_schema = Column(JSON, nullable=True)  # JSON schema for config validation
    
    # Processing settings
    max_file_size_mb = Column(Integer, default=50, nullable=False)
    processing_timeout_seconds = Column(Integer, default=300, nullable=False)
    requires_external_tool = Column(Boolean, default=False, nullable=False)
    external_tool_path = Column(String(500), nullable=True)
    
    # Status
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ExportFormatConfig(format='{self.format}', name='{self.display_name}')>"


# SQLAlchemy relationship aliases for backward compatibility
TranscriptExport = ExportJob  # Alias for existing code compatibility