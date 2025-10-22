"""
Advanced Transcript Management API Routes for T033.
Provides REST API endpoints for transcript search, versioning, tagging, 
bookmarks, batch operations, and export functionality.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from api.orm_bootstrap import get_db
from api.services.transcript_management import (
    TranscriptSearchService, TranscriptVersioningService, TranscriptTagService,
    TranscriptBookmarkService, BatchOperationService, TranscriptExportService
)
from api.services.auth import get_current_user
from api.utils.logger import get_system_logger

# Import admin security if available
try:
    from api.security.admin_access import admin_required
except ImportError:
    def admin_required(func):
        return func

logger = get_system_logger("transcript_management_api")

router = APIRouter(prefix="/transcripts", tags=["transcript-management"])


# ─── Pydantic Models ────────────────────────────────────────────────────
class TranscriptSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Text search query")
    tags: Optional[List[str]] = Field(None, description="Filter by tag names")
    status_filter: Optional[List[str]] = Field(None, description="Filter by job status")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    duration_min: Optional[int] = Field(None, description="Minimum duration in seconds")
    duration_max: Optional[int] = Field(None, description="Maximum duration in seconds")
    model_filter: Optional[List[str]] = Field(None, description="Filter by model names")
    language_filter: Optional[List[str]] = Field(None, description="Filter by languages")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class CreateVersionRequest(BaseModel):
    content: str = Field(..., description="Transcript content")
    change_summary: Optional[str] = Field(None, description="Summary of changes")


class CreateTagRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field("#3B82F6", regex=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")


class AssignTagRequest(BaseModel):
    tag_id: int = Field(..., description="Tag ID to assign")


class CreateBookmarkRequest(BaseModel):
    timestamp: float = Field(..., ge=0, description="Timestamp in seconds")
    title: str = Field(..., min_length=1, max_length=200, description="Bookmark title")
    note: Optional[str] = Field(None, description="Optional note")


class UpdateBookmarkRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Bookmark title")
    note: Optional[str] = Field(None, description="Optional note")


class BatchOperationRequest(BaseModel):
    operation_type: str = Field(..., description="Type of operation (tag, export, delete)")
    job_ids: List[str] = Field(..., min_items=1, description="List of job IDs")
    parameters: Optional[Dict] = Field(None, description="Operation-specific parameters")


class ExportRequest(BaseModel):
    job_ids: List[str] = Field(..., min_items=1, description="List of job IDs to export")
    export_format: str = Field(..., description="Export format (srt, vtt, docx, pdf, json, txt)")
    export_options: Optional[Dict] = Field(None, description="Format-specific options")


# ─── Search Endpoints ───────────────────────────────────────────────────
@router.post("/search", response_model=Dict[str, Any])
async def search_transcripts(
    search_request: TranscriptSearchRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Advanced transcript search with multiple filters and pagination."""
    try:
        result = TranscriptSearchService.search_transcripts(
            db=db,
            query=search_request.query,
            tags=search_request.tags,
            status_filter=search_request.status_filter,
            date_from=search_request.date_from,
            date_to=search_request.date_to,
            duration_min=search_request.duration_min,
            duration_max=search_request.duration_max,
            model_filter=search_request.model_filter,
            language_filter=search_request.language_filter,
            sort_by=search_request.sort_by,
            sort_order=search_request.sort_order,
            page=search_request.page,
            page_size=search_request.page_size
        )
        
        logger.info(f"User {current_user.get('username', 'unknown')} searched transcripts with query: {search_request.query}")
        return result
        
    except Exception as e:
        logger.error(f"Error searching transcripts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search transcripts")


@router.get("/filters/summary", response_model=Dict[str, Any])
async def get_filter_summary(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get summary of available filters (tags, models, languages, etc.)."""
    try:
        # Get available tags
        tags = TranscriptTagService.get_tags(db)
        
        # Get available models and languages from jobs
        from api.models import Job, TranscriptMetadata
        
        models = db.query(Job.model).distinct().all()
        languages = db.query(TranscriptMetadata.language).filter(
            TranscriptMetadata.language.isnot(None)
        ).distinct().all()
        
        # Get status counts
        from sqlalchemy import func
        status_counts = db.query(
            Job.status, func.count(Job.id)
        ).group_by(Job.status).all()
        
        return {
            "tags": [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in tags],
            "models": [model[0] for model in models if model[0]],
            "languages": [lang[0] for lang in languages if lang[0]],
            "statuses": [{"status": status.value, "count": count} for status, count in status_counts],
            "date_range": {
                "earliest": db.query(func.min(Job.created_at)).scalar(),
                "latest": db.query(func.max(Job.created_at)).scalar()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting filter summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get filter summary")


# ─── Versioning Endpoints ───────────────────────────────────────────────
@router.post("/{job_id}/versions", response_model=Dict[str, Any])
async def create_transcript_version(
    job_id: str,
    version_request: CreateVersionRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new version of a transcript."""
    try:
        version = TranscriptVersioningService.create_version(
            db=db,
            job_id=job_id,
            content=version_request.content,
            created_by=current_user.get("username"),
            change_summary=version_request.change_summary
        )
        
        return {
            "id": version.id,
            "version_number": version.version_number,
            "created_at": version.created_at.isoformat(),
            "created_by": version.created_by,
            "change_summary": version.change_summary,
            "is_current": version.is_current
        }
        
    except Exception as e:
        logger.error(f"Error creating transcript version: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create version")


@router.get("/{job_id}/versions", response_model=List[Dict[str, Any]])
async def get_transcript_versions(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get all versions for a transcript."""
    try:
        versions = TranscriptVersioningService.get_versions(db, job_id)
        
        return [
            {
                "id": version.id,
                "version_number": version.version_number,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "change_summary": version.change_summary,
                "is_current": version.is_current,
                "content_preview": version.content[:200] + "..." if len(version.content) > 200 else version.content
            }
            for version in versions
        ]
        
    except Exception as e:
        logger.error(f"Error getting transcript versions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get versions")


@router.get("/{job_id}/versions/{version_number}", response_model=Dict[str, Any])
async def get_transcript_version(
    job_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get a specific version of a transcript."""
    try:
        from api.models.transcript_management import TranscriptVersion
        from sqlalchemy import and_
        
        version = db.query(TranscriptVersion).filter(
            and_(
                TranscriptVersion.job_id == job_id,
                TranscriptVersion.version_number == version_number
            )
        ).first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {
            "id": version.id,
            "version_number": version.version_number,
            "content": version.content,
            "created_at": version.created_at.isoformat(),
            "created_by": version.created_by,
            "change_summary": version.change_summary,
            "is_current": version.is_current
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript version: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get version")


@router.post("/{job_id}/versions/{version_number}/restore", response_model=Dict[str, Any])
async def restore_transcript_version(
    job_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Restore a previous version as the current version."""
    try:
        version = TranscriptVersioningService.restore_version(
            db=db,
            job_id=job_id,
            version_number=version_number,
            restored_by=current_user.get("username")
        )
        
        return {
            "id": version.id,
            "version_number": version.version_number,
            "created_at": version.created_at.isoformat(),
            "message": f"Restored version {version_number} as current version"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring transcript version: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to restore version")


# ─── Tagging Endpoints ──────────────────────────────────────────────────
@router.get("/tags", response_model=List[Dict[str, Any]])
async def get_all_tags(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get all available tags."""
    try:
        tags = TranscriptTagService.get_tags(db)
        
        return [
            {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "created_at": tag.created_at.isoformat(),
                "created_by": tag.created_by
            }
            for tag in tags
        ]
        
    except Exception as e:
        logger.error(f"Error getting tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get tags")


@router.post("/tags", response_model=Dict[str, Any])
async def create_tag(
    tag_request: CreateTagRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a new tag."""
    try:
        tag = TranscriptTagService.create_tag(
            db=db,
            name=tag_request.name,
            color=tag_request.color,
            created_by=current_user.get("username")
        )
        
        return {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "created_at": tag.created_at.isoformat(),
            "created_by": tag.created_by
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create tag")


@router.post("/{job_id}/tags", response_model=Dict[str, Any])
async def assign_tag_to_job(
    job_id: str,
    tag_request: AssignTagRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Assign a tag to a job."""
    try:
        job_tag = TranscriptTagService.assign_tag(
            db=db,
            job_id=job_id,
            tag_id=tag_request.tag_id,
            assigned_by=current_user.get("username")
        )
        
        return {
            "job_id": job_tag.job_id,
            "tag_id": job_tag.tag_id,
            "assigned_at": job_tag.assigned_at.isoformat(),
            "assigned_by": job_tag.assigned_by,
            "message": "Tag assigned successfully"
        }
        
    except Exception as e:
        logger.error(f"Error assigning tag: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assign tag")


@router.delete("/{job_id}/tags/{tag_id}")
async def remove_tag_from_job(
    job_id: str,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Remove a tag from a job."""
    try:
        success = TranscriptTagService.remove_tag(db, job_id, tag_id)
        
        if success:
            return {"message": "Tag removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Tag assignment not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing tag: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove tag")


@router.get("/{job_id}/tags", response_model=List[Dict[str, Any]])
async def get_job_tags(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get all tags for a specific job."""
    try:
        tags = TranscriptTagService.get_job_tags(db, job_id)
        
        return [
            {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color
            }
            for tag in tags
        ]
        
    except Exception as e:
        logger.error(f"Error getting job tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get job tags")


# ─── Bookmark Endpoints ─────────────────────────────────────────────────
@router.post("/{job_id}/bookmarks", response_model=Dict[str, Any])
async def create_bookmark(
    job_id: str,
    bookmark_request: CreateBookmarkRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a bookmark for a specific timestamp in a transcript."""
    try:
        bookmark = TranscriptBookmarkService.create_bookmark(
            db=db,
            job_id=job_id,
            timestamp=bookmark_request.timestamp,
            title=bookmark_request.title,
            note=bookmark_request.note,
            created_by=current_user.get("username")
        )
        
        return {
            "id": bookmark.id,
            "job_id": bookmark.job_id,
            "timestamp": bookmark.timestamp,
            "title": bookmark.title,
            "note": bookmark.note,
            "created_at": bookmark.created_at.isoformat(),
            "created_by": bookmark.created_by
        }
        
    except Exception as e:
        logger.error(f"Error creating bookmark: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create bookmark")


@router.get("/{job_id}/bookmarks", response_model=List[Dict[str, Any]])
async def get_job_bookmarks(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get all bookmarks for a job."""
    try:
        bookmarks = TranscriptBookmarkService.get_bookmarks(db, job_id)
        
        return [
            {
                "id": bookmark.id,
                "timestamp": bookmark.timestamp,
                "title": bookmark.title,
                "note": bookmark.note,
                "created_at": bookmark.created_at.isoformat(),
                "created_by": bookmark.created_by
            }
            for bookmark in bookmarks
        ]
        
    except Exception as e:
        logger.error(f"Error getting bookmarks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get bookmarks")


@router.put("/bookmarks/{bookmark_id}", response_model=Dict[str, Any])
async def update_bookmark(
    bookmark_id: int,
    bookmark_request: UpdateBookmarkRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Update an existing bookmark."""
    try:
        bookmark = TranscriptBookmarkService.update_bookmark(
            db=db,
            bookmark_id=bookmark_id,
            title=bookmark_request.title,
            note=bookmark_request.note
        )
        
        return {
            "id": bookmark.id,
            "timestamp": bookmark.timestamp,
            "title": bookmark.title,
            "note": bookmark.note,
            "message": "Bookmark updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bookmark: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update bookmark")


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(
    bookmark_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Delete a bookmark."""
    try:
        success = TranscriptBookmarkService.delete_bookmark(db, bookmark_id)
        
        if success:
            return {"message": "Bookmark deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bookmark: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete bookmark")


# ─── Batch Operation Endpoints ──────────────────────────────────────────
@router.post("/batch", response_model=Dict[str, Any])
async def create_batch_operation(
    batch_request: BatchOperationRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create a batch operation for multiple transcripts."""
    try:
        operation = BatchOperationService.create_batch_operation(
            db=db,
            operation_type=batch_request.operation_type,
            job_ids=batch_request.job_ids,
            parameters=batch_request.parameters,
            created_by=current_user.get("username")
        )
        
        return {
            "id": operation.id,
            "operation_type": operation.operation_type,
            "status": operation.status,
            "job_count": len(operation.job_ids),
            "created_at": operation.created_at.isoformat(),
            "message": "Batch operation created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating batch operation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create batch operation")


@router.get("/batch", response_model=List[Dict[str, Any]])
async def get_batch_operations(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get batch operations for the current user."""
    try:
        operations = BatchOperationService.get_batch_operations(
            db=db,
            created_by=current_user.get("username")
        )
        
        return [
            {
                "id": operation.id,
                "operation_type": operation.operation_type,
                "status": operation.status,
                "job_count": len(operation.job_ids),
                "created_at": operation.created_at.isoformat(),
                "started_at": operation.started_at.isoformat() if operation.started_at else None,
                "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
                "error_message": operation.error_message
            }
            for operation in operations
        ]
        
    except Exception as e:
        logger.error(f"Error getting batch operations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get batch operations")


# ─── Export Endpoints ───────────────────────────────────────────────────
@router.post("/export", response_model=Dict[str, Any])
async def create_export(
    export_request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Create an export operation for transcripts."""
    try:
        export = TranscriptExportService.create_export(
            db=db,
            job_ids=export_request.job_ids,
            export_format=export_request.export_format,
            export_options=export_request.export_options,
            created_by=current_user.get("username")
        )
        
        return {
            "id": export.id,
            "export_format": export.export_format,
            "job_count": len(export.job_ids),
            "created_at": export.created_at.isoformat(),
            "expires_at": export.expires_at.isoformat() if export.expires_at else None,
            "message": "Export created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create export")


@router.get("/exports", response_model=List[Dict[str, Any]])
async def get_exports(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get export operations for the current user."""
    try:
        exports = TranscriptExportService.get_exports(
            db=db,
            created_by=current_user.get("username")
        )
        
        return [
            {
                "id": export.id,
                "export_format": export.export_format,
                "job_count": len(export.job_ids),
                "download_count": export.download_count,
                "created_at": export.created_at.isoformat(),
                "expires_at": export.expires_at.isoformat() if export.expires_at else None,
                "file_ready": export.file_path is not None
            }
            for export in exports
        ]
        
    except Exception as e:
        logger.error(f"Error getting exports: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get exports")


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Download an exported file."""
    try:
        # This would be implemented with actual file serving logic
        # For now, return a placeholder response
        export = TranscriptExportService.increment_download_count(db, export_id)
        
        return {
            "message": "Download would start here",
            "export_id": export_id,
            "download_count": export.download_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download export")