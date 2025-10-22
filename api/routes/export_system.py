"""
FastAPI routes for T034 Multi-Format Export System.
Provides comprehensive API endpoints for export operations, template management, and batch processing.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..database import get_db
from ..auth import get_current_user, require_admin
from ..models.export_system import (
    ExportTemplate, ExportJob, BatchExport, ExportHistory, ExportFormatConfig,
    ExportFormat, ExportStatus, BatchExportStatus, TemplateType
)
from ..services.export_system import (
    ExportFormatService, ExportTemplateService, ExportJobService, BatchExportService
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/exports", tags=["Export System"])


# Pydantic Models for Request/Response

class ExportFormatResponse(BaseModel):
    """Response model for export format information."""
    format: str
    display_name: str
    file_extension: str
    mime_type: str
    supports_timestamps: bool
    supports_styling: bool
    supports_metadata: bool
    max_file_size_mb: int
    default_config: Dict[str, Any]

class ExportTemplateCreate(BaseModel):
    """Request model for creating export templates."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_type: str = Field(..., description="Template type: subtitle, document, structured, plain_text")
    supported_formats: List[str] = Field(..., min_items=1, description="List of supported export formats")
    template_config: Dict[str, Any] = Field(..., description="Template configuration options")
    styling_config: Optional[Dict[str, Any]] = Field(None, description="Styling configuration for documents")
    layout_config: Optional[Dict[str, Any]] = Field(None, description="Layout configuration")

    @validator('template_type')
    def validate_template_type(cls, v):
        valid_types = [t.value for t in TemplateType]
        if v not in valid_types:
            raise ValueError(f"Invalid template type. Must be one of: {valid_types}")
        return v

    @validator('supported_formats')
    def validate_supported_formats(cls, v):
        valid_formats = [f.value for f in ExportFormat]
        invalid_formats = [fmt for fmt in v if fmt not in valid_formats]
        if invalid_formats:
            raise ValueError(f"Invalid export formats: {invalid_formats}. Must be one of: {valid_formats}")
        return v

class ExportTemplateResponse(BaseModel):
    """Response model for export templates."""
    id: int
    name: str
    description: Optional[str]
    template_type: str
    supported_formats: List[str]
    template_config: Dict[str, Any]
    styling_config: Optional[Dict[str, Any]]
    layout_config: Optional[Dict[str, Any]]
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_system_template: bool
    is_active: bool
    usage_count: int
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True

class ExportJobCreate(BaseModel):
    """Request model for creating individual export jobs."""
    job_id: str = Field(..., description="ID of the transcript job to export")
    format: str = Field(..., description="Export format")
    template_id: Optional[int] = Field(None, description="Template ID to use")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Custom export configuration")

    @validator('format')
    def validate_format(cls, v):
        valid_formats = [f.value for f in ExportFormat]
        if v not in valid_formats:
            raise ValueError(f"Invalid export format. Must be one of: {valid_formats}")
        return v

class ExportJobResponse(BaseModel):
    """Response model for export jobs."""
    id: int
    job_id: str
    batch_export_id: Optional[int]
    format: str
    template_id: Optional[int]
    custom_config: Optional[Dict[str, Any]]
    status: str
    progress_percentage: float
    output_filename: Optional[str]
    output_path: Optional[str]
    output_url: Optional[str]
    output_size_bytes: Optional[int]
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_duration_seconds: Optional[float]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    created_by: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

class BatchExportCreate(BaseModel):
    """Request model for creating batch export operations."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    job_ids: List[str] = Field(..., min_items=1, max_items=100, description="List of job IDs to export")
    export_format: str = Field(..., description="Export format for all jobs")
    template_id: Optional[int] = Field(None, description="Template ID to use")
    batch_config: Optional[Dict[str, Any]] = Field(None, description="Batch-specific configuration")

    @validator('export_format')
    def validate_export_format(cls, v):
        valid_formats = [f.value for f in ExportFormat]
        if v not in valid_formats:
            raise ValueError(f"Invalid export format. Must be one of: {valid_formats}")
        return v

class BatchExportResponse(BaseModel):
    """Response model for batch exports."""
    id: int
    name: str
    description: Optional[str]
    export_format: str
    template_id: Optional[int]
    batch_config: Optional[Dict[str, Any]]
    job_ids: List[str]
    filter_criteria: Optional[Dict[str, Any]]
    status: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    progress_percentage: float
    archive_filename: Optional[str]
    archive_path: Optional[str]
    archive_size_bytes: Optional[int]
    download_url: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_duration_seconds: Optional[float]
    error_message: Optional[str]
    partial_success: bool
    created_by: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

class ExportHistoryResponse(BaseModel):
    """Response model for export history."""
    id: int
    export_job_id: Optional[int]
    batch_export_id: Optional[int]
    export_type: str
    format: str
    template_name: Optional[str]
    user_id: Optional[str]
    user_email: Optional[str]
    processing_time_seconds: Optional[float]
    output_size_bytes: Optional[int]
    job_count: int
    success: bool
    error_type: Optional[str]
    error_details: Optional[str]
    exported_at: datetime
    downloaded_at: Optional[datetime]

    class Config:
        from_attributes = True


# Export Format Endpoints

@router.get("/formats", response_model=List[ExportFormatResponse])
async def get_available_formats(db: Session = Depends(get_db)):
    """Get all available export formats with their configurations."""
    try:
        formats = ExportFormatService.get_available_formats(db)
        return formats
    except Exception as e:
        logger.error(f"Error retrieving export formats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export formats")

@router.get("/formats/{format_name}")
async def get_format_details(
    format_name: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific export format."""
    try:
        format_config = ExportFormatService.get_format_config(db, format_name)
        if not format_config:
            raise HTTPException(status_code=404, detail=f"Export format '{format_name}' not found")
        
        return {
            "format": format_config.format,
            "display_name": format_config.display_name,
            "file_extension": format_config.file_extension,
            "mime_type": format_config.mime_type,
            "supports_timestamps": format_config.supports_timestamps,
            "supports_styling": format_config.supports_styling,
            "supports_metadata": format_config.supports_metadata,
            "default_config": format_config.default_config,
            "validation_schema": format_config.validation_schema,
            "max_file_size_mb": format_config.max_file_size_mb,
            "processing_timeout_seconds": format_config.processing_timeout_seconds,
            "is_enabled": format_config.is_enabled
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving format details for {format_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve format details")


# Export Template Endpoints

@router.get("/templates", response_model=List[ExportTemplateResponse])
async def get_templates(
    format_filter: Optional[str] = Query(None, description="Filter templates by supported format"),
    system_only: bool = Query(False, description="Return only system templates"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get export templates, optionally filtered by format."""
    try:
        if system_only:
            templates = ExportTemplateService.get_system_templates(db)
        elif format_filter:
            templates = ExportTemplateService.get_templates_for_format(db, format_filter)
        else:
            templates = db.query(ExportTemplate).filter(ExportTemplate.is_active == True).all()
        
        return templates
    except Exception as e:
        logger.error(f"Error retrieving templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")

@router.post("/templates", response_model=ExportTemplateResponse)
async def create_template(
    template_data: ExportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new export template."""
    try:
        template = ExportTemplateService.create_template(
            db=db,
            name=template_data.name,
            description=template_data.description,
            template_type=template_data.template_type,
            supported_formats=template_data.supported_formats,
            template_config=template_data.template_config,
            styling_config=template_data.styling_config,
            layout_config=template_data.layout_config,
            created_by=current_user.get("sub")
        )
        return template
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create template")

@router.get("/templates/{template_id}", response_model=ExportTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific template."""
    template = db.query(ExportTemplate).filter(ExportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete or deactivate a template."""
    template = db.query(ExportTemplate).filter(ExportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Check permissions
    if template.is_system_template and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Cannot delete system templates")
    
    if template.created_by != current_user.get("sub") and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Can only delete your own templates")
    
    # Soft delete by deactivating
    template.is_active = False
    db.commit()
    
    return {"message": "Template deleted successfully"}


# Individual Export Job Endpoints

@router.post("/jobs", response_model=ExportJobResponse)
async def create_export_job(
    export_data: ExportJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new export job for a single transcript."""
    try:
        # Validate job exists and user has access
        from ..models import Job
        job = db.query(Job).filter(Job.id == export_data.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Transcript job not found")
        
        # Check job ownership (unless admin)
        if job.user_id != current_user.get("sub") and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Access denied to this transcript job")
        
        # Create export job
        export_job = ExportJobService.create_export_job(
            db=db,
            job_id=export_data.job_id,
            format=export_data.format,
            template_id=export_data.template_id,
            custom_config=export_data.custom_config,
            created_by=current_user.get("sub")
        )
        
        # Process export in background
        background_tasks.add_task(ExportJobService.process_export_job, db, export_job.id)
        
        return export_job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create export job")

@router.get("/jobs/{export_job_id}", response_model=ExportJobResponse)
async def get_export_job(
    export_job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific export job."""
    export_job = db.query(ExportJob).filter(ExportJob.id == export_job_id).first()
    if not export_job:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    # Check access permissions
    if export_job.created_by != current_user.get("sub") and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Access denied to this export job")
    
    return export_job

@router.get("/jobs", response_model=List[ExportJobResponse])
async def get_user_export_jobs(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    format_filter: Optional[str] = Query(None, description="Filter by format"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's export jobs with optional filtering."""
    try:
        query = db.query(ExportJob)
        
        # Filter by user (unless admin viewing all)
        if not current_user.get("is_admin", False):
            query = query.filter(ExportJob.created_by == current_user.get("sub"))
        
        # Apply filters
        if status_filter:
            query = query.filter(ExportJob.status == status_filter)
        if format_filter:
            query = query.filter(ExportJob.format == format_filter)
        
        # Pagination
        offset = (page - 1) * page_size
        export_jobs = query.order_by(ExportJob.created_at.desc()).offset(offset).limit(page_size).all()
        
        return export_jobs
    except Exception as e:
        logger.error(f"Error retrieving export jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export jobs")

@router.get("/jobs/{export_job_id}/download")
async def download_export(
    export_job_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download the export file."""
    export_job = db.query(ExportJob).filter(ExportJob.id == export_job_id).first()
    if not export_job:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    # Check access permissions
    if export_job.created_by != current_user.get("sub") and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Access denied to this export job")
    
    # Check if export is complete
    if export_job.status != ExportStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Export is not completed yet")
    
    # Check if file exists
    if not export_job.output_path or not os.path.exists(export_job.output_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    
    # Update download timestamp
    history = db.query(ExportHistory).filter(ExportHistory.export_job_id == export_job_id).first()
    if history:
        history.downloaded_at = datetime.utcnow()
        db.commit()
    
    # Get format configuration for mime type
    format_config = ExportFormatService.get_format_config(db, export_job.format)
    mime_type = format_config.mime_type if format_config else "application/octet-stream"
    
    return FileResponse(
        path=export_job.output_path,
        filename=export_job.output_filename,
        media_type=mime_type
    )


# Batch Export Endpoints

@router.post("/batch", response_model=BatchExportResponse)
async def create_batch_export(
    batch_data: BatchExportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new batch export operation."""
    try:
        # Validate jobs exist and user has access
        from ..models import Job
        jobs = db.query(Job).filter(Job.id.in_(batch_data.job_ids)).all()
        found_job_ids = [job.id for job in jobs]
        
        # Check for missing jobs
        missing_jobs = set(batch_data.job_ids) - set(found_job_ids)
        if missing_jobs:
            raise HTTPException(status_code=404, detail=f"Jobs not found: {missing_jobs}")
        
        # Check access permissions (unless admin)
        if not current_user.get("is_admin", False):
            user_jobs = [job for job in jobs if job.user_id == current_user.get("sub")]
            if len(user_jobs) != len(jobs):
                raise HTTPException(status_code=403, detail="Access denied to some transcript jobs")
        
        # Create batch export
        batch_export = BatchExportService.create_batch_export(
            db=db,
            name=batch_data.name,
            job_ids=batch_data.job_ids,
            export_format=batch_data.export_format,
            template_id=batch_data.template_id,
            batch_config=batch_data.batch_config,
            created_by=current_user.get("sub"),
            description=batch_data.description
        )
        
        # Process batch export in background
        background_tasks.add_task(BatchExportService.process_batch_export, db, batch_export.id)
        
        return batch_export
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create batch export")

@router.get("/batch/{batch_export_id}", response_model=BatchExportResponse)
async def get_batch_export(
    batch_export_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get details of a specific batch export."""
    batch_export = db.query(BatchExport).filter(BatchExport.id == batch_export_id).first()
    if not batch_export:
        raise HTTPException(status_code=404, detail="Batch export not found")
    
    # Check access permissions
    if batch_export.created_by != current_user.get("sub") and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Access denied to this batch export")
    
    return batch_export

@router.get("/batch", response_model=List[BatchExportResponse])
async def get_user_batch_exports(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    format_filter: Optional[str] = Query(None, description="Filter by format"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's batch exports with optional filtering."""
    try:
        query = db.query(BatchExport)
        
        # Filter by user (unless admin viewing all)
        if not current_user.get("is_admin", False):
            query = query.filter(BatchExport.created_by == current_user.get("sub"))
        
        # Apply filters
        if status_filter:
            query = query.filter(BatchExport.status == status_filter)
        if format_filter:
            query = query.filter(BatchExport.export_format == format_filter)
        
        # Pagination
        offset = (page - 1) * page_size
        batch_exports = query.order_by(BatchExport.created_at.desc()).offset(offset).limit(page_size).all()
        
        return batch_exports
    except Exception as e:
        logger.error(f"Error retrieving batch exports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve batch exports")

@router.get("/batch/{batch_export_id}/download")
async def download_batch_export(
    batch_export_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download the batch export archive."""
    batch_export = db.query(BatchExport).filter(BatchExport.id == batch_export_id).first()
    if not batch_export:
        raise HTTPException(status_code=404, detail="Batch export not found")
    
    # Check access permissions
    if batch_export.created_by != current_user.get("sub") and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Access denied to this batch export")
    
    # Check if batch export is complete
    if not batch_export.is_complete():
        raise HTTPException(status_code=400, detail="Batch export is not completed yet")
    
    # Check if archive exists
    if not batch_export.archive_path or not os.path.exists(batch_export.archive_path):
        raise HTTPException(status_code=404, detail="Batch export archive not found")
    
    # Update download timestamp
    history = db.query(ExportHistory).filter(ExportHistory.batch_export_id == batch_export_id).first()
    if history:
        history.downloaded_at = datetime.utcnow()
        db.commit()
    
    return FileResponse(
        path=batch_export.archive_path,
        filename=batch_export.archive_filename,
        media_type="application/zip"
    )


# Export History Endpoints

@router.get("/history", response_model=List[ExportHistoryResponse])
async def get_export_history(
    export_type: Optional[str] = Query(None, description="Filter by export type: single or batch"),
    format_filter: Optional[str] = Query(None, description="Filter by format"),
    success_only: bool = Query(False, description="Show only successful exports"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get export history with optional filtering."""
    try:
        query = db.query(ExportHistory)
        
        # Filter by user (unless admin viewing all)
        if not current_user.get("is_admin", False):
            query = query.filter(ExportHistory.user_id == current_user.get("sub"))
        
        # Apply filters
        if export_type:
            query = query.filter(ExportHistory.export_type == export_type)
        if format_filter:
            query = query.filter(ExportHistory.format == format_filter)
        if success_only:
            query = query.filter(ExportHistory.success == True)
        
        # Pagination
        offset = (page - 1) * page_size
        history_records = query.order_by(ExportHistory.exported_at.desc()).offset(offset).limit(page_size).all()
        
        return history_records
    except Exception as e:
        logger.error(f"Error retrieving export history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export history")


# Admin Endpoints

@router.get("/admin/stats")
async def get_export_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get export system statistics (admin only)."""
    try:
        from sqlalchemy import func
        
        # Overall statistics
        total_exports = db.query(ExportHistory).count()
        successful_exports = db.query(ExportHistory).filter(ExportHistory.success == True).count()
        failed_exports = total_exports - successful_exports
        
        # Format statistics
        format_stats = db.query(
            ExportHistory.format,
            func.count(ExportHistory.id).label('count'),
            func.avg(ExportHistory.processing_time_seconds).label('avg_time')
        ).group_by(ExportHistory.format).all()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_exports = db.query(ExportHistory).filter(
            ExportHistory.exported_at >= thirty_days_ago
        ).count()
        
        # Active jobs
        active_individual = db.query(ExportJob).filter(
            ExportJob.status.in_([ExportStatus.PENDING.value, ExportStatus.PROCESSING.value])
        ).count()
        
        active_batch = db.query(BatchExport).filter(
            BatchExport.status.in_([
                BatchExportStatus.CREATED.value,
                BatchExportStatus.QUEUED.value,
                BatchExportStatus.PROCESSING.value
            ])
        ).count()
        
        return {
            "total_exports": total_exports,
            "successful_exports": successful_exports,
            "failed_exports": failed_exports,
            "success_rate": (successful_exports / total_exports * 100) if total_exports > 0 else 0,
            "recent_exports_30d": recent_exports,
            "active_individual_jobs": active_individual,
            "active_batch_jobs": active_batch,
            "format_statistics": [
                {
                    "format": stat.format,
                    "count": stat.count,
                    "average_processing_time": round(stat.avg_time, 2) if stat.avg_time else None
                }
                for stat in format_stats
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving export statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.post("/admin/templates/create-defaults")
async def create_default_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create default system templates (admin only)."""
    try:
        ExportTemplateService.create_default_templates(db)
        return {"message": "Default templates created successfully"}
    except Exception as e:
        logger.error(f"Error creating default templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create default templates")

@router.delete("/admin/cleanup-expired")
async def cleanup_expired_exports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Clean up expired export files and records (admin only)."""
    try:
        # Find expired export jobs
        expired_jobs = db.query(ExportJob).filter(
            ExportJob.expires_at < datetime.utcnow()
        ).all()
        
        # Find expired batch exports
        expired_batches = db.query(BatchExport).filter(
            BatchExport.expires_at < datetime.utcnow()
        ).all()
        
        cleanup_count = 0
        
        # Clean up individual export files
        for job in expired_jobs:
            if job.output_path and os.path.exists(job.output_path):
                try:
                    os.unlink(job.output_path)
                    cleanup_count += 1
                except OSError:
                    pass
            db.delete(job)
        
        # Clean up batch export archives
        for batch in expired_batches:
            if batch.archive_path and os.path.exists(batch.archive_path):
                try:
                    os.unlink(batch.archive_path)
                    cleanup_count += 1
                except OSError:
                    pass
            db.delete(batch)
        
        db.commit()
        
        return {
            "message": f"Cleanup completed",
            "expired_individual_jobs": len(expired_jobs),
            "expired_batch_jobs": len(expired_batches),
            "files_removed": cleanup_count
        }
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup expired exports")


# Initialize default format configurations
@router.on_event("startup")
async def initialize_export_formats():
    """Initialize default export format configurations."""
    # This would typically be handled by a database migration
    # but included here for completeness
    pass