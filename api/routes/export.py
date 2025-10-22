"""
T022: Multi-Format Export System - API Routes
RESTful endpoints for transcript export functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import io
from datetime import datetime
import logging

from api.database import get_db
from api.models import Job, User
from api.auth import get_current_user
from api.services.transcript_export import (
    transcript_export_service,
    ExportFormat,
    ExportOptions,
    ExportTemplate
)
from api.schemas import BaseResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


# Request/Response Models
class ExportRequest(BaseModel):
    """Request model for transcript export"""
    job_id: str = Field(..., description="Job ID to export")
    format: str = Field(..., description="Export format (srt, vtt, docx, pdf, json, txt)")
    template_name: Optional[str] = Field(None, description="Template name to use")
    custom_filename: Optional[str] = Field(None, description="Custom filename for export")
    options: Optional[Dict[str, Any]] = Field(None, description="Custom export options")


class ExportResponse(BaseResponse):
    """Response model for export operations"""
    format: str
    filename: str
    file_size: int
    download_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FormatInfo(BaseModel):
    """Information about an export format"""
    format: str
    name: str
    available: bool
    description: str
    requires: List[str]


class TemplateInfo(BaseModel):
    """Information about an export template"""
    name: str
    format: str
    description: str
    include_timestamps: bool
    include_metadata: bool
    include_summary: bool
    include_keywords: bool


class BatchExportRequest(BaseModel):
    """Request model for batch export"""
    job_ids: List[str] = Field(..., description="List of job IDs to export")
    format: str = Field(..., description="Export format for all jobs")
    template_name: Optional[str] = Field(None, description="Template to use for all exports")
    zip_filename: Optional[str] = Field(None, description="Name for the ZIP archive")


class BatchExportResponse(BaseResponse):
    """Response model for batch export"""
    batch_id: str
    total_jobs: int
    successful_exports: int
    failed_exports: int
    zip_filename: str
    zip_size: int
    download_url: str


@router.get("/formats", response_model=List[FormatInfo])
async def get_available_formats():
    """Get list of available export formats"""
    try:
        formats = transcript_export_service.get_available_formats()
        return formats
    except Exception as e:
        logger.error(f"Error fetching export formats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch export formats")


@router.get("/templates", response_model=List[TemplateInfo])
async def get_export_templates(format: Optional[str] = Query(None, description="Filter by format")):
    """Get available export templates"""
    try:
        format_enum = None
        if format:
            try:
                format_enum = ExportFormat(format.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
        
        templates = transcript_export_service.get_templates(format_filter=format_enum)
        return templates
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching export templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch export templates")


@router.post("/export", response_model=ExportResponse)
async def export_transcript(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export a transcript to specified format"""
    try:
        # Validate format
        try:
            export_format = ExportFormat(request.format.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid export format: {request.format}")
        
        # Get job and verify ownership
        job = db.query(Job).filter(Job.id == request.job_id, Job.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        # Check if job is completed
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job must be completed to export")
        
        # Prepare export options
        export_options = ExportOptions()
        if request.custom_filename:
            export_options.custom_filename = request.custom_filename
        
        # Apply custom options if provided
        if request.options:
            for key, value in request.options.items():
                if hasattr(export_options, key):
                    setattr(export_options, key, value)
        
        # Set template if specified
        if request.template_name:
            templates = transcript_export_service.get_templates(format_filter=export_format)
            template = next((t for t in templates if t["name"] == request.template_name), None)
            if template:
                export_options.template = ExportTemplate(**template)
        
        # Perform export
        result = transcript_export_service.export_transcript(job, export_format, export_options)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Export failed: {result.error}")
        
        # Store export result for download (in a real implementation, you might save to file system or S3)
        download_url = f"/api/export/download/{job.id}/{export_format.value}"
        
        logger.info(f"Successfully exported transcript {job.id} for user {current_user.id} in {export_format.value} format")
        
        return ExportResponse(
            success=True,
            message="Transcript exported successfully",
            format=result.format.value,
            filename=result.filename,
            file_size=result.file_size,
            download_url=download_url,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting transcript {request.job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Export operation failed")


@router.get("/download/{job_id}/{format}")
async def download_export(
    job_id: str,
    format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    template: Optional[str] = Query(None, description="Template name")
):
    """Download exported transcript file"""
    try:
        # Validate format
        try:
            export_format = ExportFormat(format.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid export format: {format}")
        
        # Get job and verify ownership
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        # Check if job is completed
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job must be completed to export")
        
        # Prepare export options
        export_options = ExportOptions()
        if template:
            templates = transcript_export_service.get_templates(format_filter=export_format)
            template_info = next((t for t in templates if t["name"] == template), None)
            if template_info:
                export_options.template = ExportTemplate(**template_info)
        
        # Perform export
        result = transcript_export_service.export_transcript(job, export_format, export_options)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Export failed: {result.error}")
        
        # Determine content type
        content_types = {
            ExportFormat.SRT: "application/x-subrip",
            ExportFormat.VTT: "text/vtt",
            ExportFormat.JSON: "application/json",
            ExportFormat.TXT: "text/plain",
            ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ExportFormat.PDF: "application/pdf"
        }
        content_type = content_types.get(export_format, "application/octet-stream")
        
        # Create response
        if isinstance(result.content, str):
            content = result.content.encode('utf-8')
        else:
            content = result.content
        
        response = StreamingResponse(
            io.BytesIO(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={result.filename}",
                "Content-Length": str(result.file_size)
            }
        )
        
        logger.info(f"Downloaded export {job_id} in {format} format for user {current_user.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export {job_id}/{format}: {str(e)}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.post("/batch", response_model=BatchExportResponse)
async def batch_export_transcripts(
    request: BatchExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export multiple transcripts in a batch"""
    try:
        # Validate format
        try:
            export_format = ExportFormat(request.format.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid export format: {request.format}")
        
        # Validate job limit
        if len(request.job_ids) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 jobs per batch export")
        
        # Get jobs and verify ownership
        jobs = db.query(Job).filter(
            Job.id.in_(request.job_ids),
            Job.user_id == current_user.id,
            Job.status == "completed"
        ).all()
        
        if not jobs:
            raise HTTPException(status_code=404, detail="No valid completed jobs found")
        
        # Prepare export options
        export_options = ExportOptions()
        if request.template_name:
            templates = transcript_export_service.get_templates(format_filter=export_format)
            template_info = next((t for t in templates if t["name"] == request.template_name), None)
            if template_info:
                export_options.template = ExportTemplate(**template_info)
        
        # Perform batch export
        successful_exports = 0
        failed_exports = 0
        export_results = []
        
        for job in jobs:
            try:
                result = transcript_export_service.export_transcript(job, export_format, export_options)
                if result.success:
                    successful_exports += 1
                    export_results.append(result)
                else:
                    failed_exports += 1
                    logger.warning(f"Failed to export job {job.id}: {result.error}")
            except Exception as e:
                failed_exports += 1
                logger.error(f"Error exporting job {job.id}: {str(e)}")
        
        # Create ZIP archive (simplified - in production, save to file system)
        import zipfile
        zip_buffer = io.BytesIO()
        zip_filename = request.zip_filename or f"batch_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result in export_results:
                if isinstance(result.content, str):
                    content = result.content.encode('utf-8')
                else:
                    content = result.content
                zip_file.writestr(result.filename, content)
        
        zip_buffer.seek(0)
        zip_size = len(zip_buffer.getvalue())
        
        # Generate batch ID and download URL
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        download_url = f"/api/export/batch/download/{batch_id}"
        
        logger.info(f"Batch export completed for user {current_user.id}: {successful_exports} successful, {failed_exports} failed")
        
        return BatchExportResponse(
            success=True,
            message=f"Batch export completed: {successful_exports} successful, {failed_exports} failed",
            batch_id=batch_id,
            total_jobs=len(request.job_ids),
            successful_exports=successful_exports,
            failed_exports=failed_exports,
            zip_filename=zip_filename,
            zip_size=zip_size,
            download_url=download_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch export: {str(e)}")
        raise HTTPException(status_code=500, detail="Batch export failed")


@router.get("/preview/{job_id}/{format}")
async def preview_export(
    job_id: str,
    format: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    template: Optional[str] = Query(None, description="Template name"),
    lines: int = Query(10, description="Number of lines to preview")
):
    """Preview export format without downloading full file"""
    try:
        # Validate format
        try:
            export_format = ExportFormat(format.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid export format: {format}")
        
        # Get job and verify ownership
        job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
        
        # Check if job is completed
        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job must be completed to preview export")
        
        # Create a temporary job with truncated content for preview
        preview_content = "\n".join(job.transcript_content.split('\n')[:lines])
        
        # Prepare export options
        export_options = ExportOptions()
        if template:
            templates = transcript_export_service.get_templates(format_filter=export_format)
            template_info = next((t for t in templates if t["name"] == template), None)
            if template_info:
                export_options.template = ExportTemplate(**template_info)
        
        # Create preview job
        preview_job = Job(
            id=job.id,
            original_filename=job.original_filename,
            transcript_content=preview_content,
            transcript_metadata=job.transcript_metadata,
            status=job.status,
            created_at=job.created_at
        )
        
        # Perform export
        result = transcript_export_service.export_transcript(preview_job, export_format, export_options)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Preview generation failed: {result.error}")
        
        # Return preview content as text
        if isinstance(result.content, bytes):
            preview_text = result.content.decode('utf-8', errors='ignore')
        else:
            preview_text = result.content
        
        return {
            "success": True,
            "format": export_format.value,
            "preview": preview_text,
            "lines_shown": lines,
            "total_estimated_size": result.file_size * (len(job.transcript_content.split('\n')) / lines) if lines > 0 else result.file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating export preview {job_id}/{format}: {str(e)}")
        raise HTTPException(status_code=500, detail="Preview generation failed")


@router.get("/stats", response_model=Dict[str, Any])
async def get_export_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get export statistics for the current user"""
    try:
        # Get user's completed jobs count
        completed_jobs = db.query(Job).filter(
            Job.user_id == current_user.id,
            Job.status == "completed"
        ).count()
        
        # Get available formats
        formats = transcript_export_service.get_available_formats()
        available_formats = [f for f in formats if f["available"]]
        
        # Get templates
        templates = transcript_export_service.get_templates()
        
        stats = {
            "available_jobs": completed_jobs,
            "available_formats": len(available_formats),
            "available_templates": len(templates),
            "formats": available_formats,
            "templates": templates,
            "batch_limit": 50,
            "supported_features": {
                "single_export": True,
                "batch_export": True,
                "format_preview": True,
                "custom_templates": True,
                "download_links": True
            }
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching export stats for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch export statistics")