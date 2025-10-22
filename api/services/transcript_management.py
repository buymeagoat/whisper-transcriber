"""
Advanced Transcript Management Service for T033.
Provides comprehensive transcript management capabilities including search, 
versioning, tagging, batch operations, and export functionality.
"""

import uuid
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException

from api.models import Job, JobStatusEnum, TranscriptMetadata
from api.models.transcript_management import (
    TranscriptVersion, TranscriptTag, JobTag, TranscriptBookmark,
    TranscriptSearchIndex, BatchOperation, TranscriptExport
)
from api.utils.logger import get_system_logger

logger = get_system_logger("transcript_management")


class TranscriptSearchService:
    """Service for advanced transcript search and filtering."""
    
    @staticmethod
    def search_transcripts(
        db: Session,
        query: str = "",
        tags: List[str] = None,
        status_filter: List[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        duration_min: Optional[int] = None,
        duration_max: Optional[int] = None,
        model_filter: List[str] = None,
        language_filter: List[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Advanced search with multiple filters and sorting options.
        
        Args:
            query: Text search in transcript content and metadata
            tags: List of tag names to filter by
            status_filter: List of job statuses to include
            date_from/date_to: Date range filter
            duration_min/max: Duration range filter (seconds)
            model_filter: List of models to filter by
            language_filter: List of languages to filter by
            sort_by: Field to sort by (created_at, duration, filename, etc.)
            sort_order: "asc" or "desc"
            page/page_size: Pagination
        """
        
        # Base query joining all necessary tables
        base_query = db.query(Job).join(
            TranscriptMetadata, Job.id == TranscriptMetadata.job_id, isouter=True
        )
        
        # Text search in transcript content and metadata
        if query:
            search_conditions = []
            
            # Search in transcript content (if available)
            if hasattr(Job, 'transcript'):
                search_conditions.append(Job.transcript.ilike(f"%{query}%"))
            
            # Search in metadata fields
            search_conditions.extend([
                TranscriptMetadata.abstract.ilike(f"%{query}%"),
                TranscriptMetadata.keywords.ilike(f"%{query}%"),
                TranscriptMetadata.summary.ilike(f"%{query}%"),
                Job.original_filename.ilike(f"%{query}%")
            ])
            
            base_query = base_query.filter(or_(*search_conditions))
        
        # Tag filtering
        if tags:
            tag_subquery = db.query(JobTag.job_id).join(
                TranscriptTag, JobTag.tag_id == TranscriptTag.id
            ).filter(TranscriptTag.name.in_(tags))
            
            base_query = base_query.filter(Job.id.in_(tag_subquery))
        
        # Status filtering
        if status_filter:
            status_enums = [JobStatusEnum(status) for status in status_filter if status in JobStatusEnum._value2member_map_]
            if status_enums:
                base_query = base_query.filter(Job.status.in_(status_enums))
        
        # Date range filtering
        if date_from:
            base_query = base_query.filter(Job.created_at >= date_from)
        if date_to:
            base_query = base_query.filter(Job.created_at <= date_to)
        
        # Duration filtering
        if duration_min is not None:
            base_query = base_query.filter(TranscriptMetadata.duration >= duration_min)
        if duration_max is not None:
            base_query = base_query.filter(TranscriptMetadata.duration <= duration_max)
        
        # Model filtering
        if model_filter:
            base_query = base_query.filter(Job.model.in_(model_filter))
        
        # Language filtering
        if language_filter:
            base_query = base_query.filter(TranscriptMetadata.language.in_(language_filter))
        
        # Get total count before pagination
        total_count = base_query.count()
        
        # Sorting
        sort_field = getattr(Job, sort_by, None) or getattr(TranscriptMetadata, sort_by, Job.created_at)
        if sort_order == "desc":
            base_query = base_query.order_by(desc(sort_field))
        else:
            base_query = base_query.order_by(sort_field)
        
        # Pagination
        offset = (page - 1) * page_size
        jobs = base_query.offset(offset).limit(page_size).all()
        
        # Format results
        results = []
        for job in jobs:
            job_data = {
                "id": job.id,
                "original_filename": job.original_filename,
                "status": job.status.value,
                "model": job.model,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            }
            
            # Add metadata if available
            if hasattr(job, 'transcript_metadata') and job.transcript_metadata:
                metadata = job.transcript_metadata[0] if isinstance(job.transcript_metadata, list) else job.transcript_metadata
                job_data.update({
                    "duration": metadata.duration,
                    "tokens": metadata.tokens,
                    "language": metadata.language,
                    "wpm": metadata.wpm,
                    "abstract": metadata.abstract[:200] + "..." if len(metadata.abstract or "") > 200 else metadata.abstract,
                })
            
            # Add tags
            job_tags = db.query(TranscriptTag).join(JobTag).filter(JobTag.job_id == job.id).all()
            job_data["tags"] = [{"name": tag.name, "color": tag.color} for tag in job_tags]
            
            results.append(job_data)
        
        return {
            "results": results,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": page * page_size < total_count,
            "has_prev": page > 1
        }


class TranscriptVersioningService:
    """Service for transcript version management."""
    
    @staticmethod
    def create_version(
        db: Session,
        job_id: str,
        content: str,
        created_by: Optional[str] = None,
        change_summary: Optional[str] = None
    ) -> TranscriptVersion:
        """Create a new version of a transcript."""
        
        # Get current version number
        latest_version = db.query(TranscriptVersion).filter(
            TranscriptVersion.job_id == job_id
        ).order_by(desc(TranscriptVersion.version_number)).first()
        
        next_version = (latest_version.version_number + 1) if latest_version else 1
        
        # Mark all previous versions as not current
        db.query(TranscriptVersion).filter(
            and_(TranscriptVersion.job_id == job_id, TranscriptVersion.is_current == True)
        ).update({"is_current": False})
        
        # Create new version
        version = TranscriptVersion(
            job_id=job_id,
            version_number=next_version,
            content=content,
            created_by=created_by,
            change_summary=change_summary,
            is_current=True
        )
        
        db.add(version)
        db.commit()
        db.refresh(version)
        
        # Update search index
        TranscriptSearchService.update_search_index(db, job_id, content)
        
        logger.info(f"Created transcript version {next_version} for job {job_id}")
        return version
    
    @staticmethod
    def get_versions(db: Session, job_id: str) -> List[TranscriptVersion]:
        """Get all versions for a transcript."""
        return db.query(TranscriptVersion).filter(
            TranscriptVersion.job_id == job_id
        ).order_by(desc(TranscriptVersion.version_number)).all()
    
    @staticmethod
    def get_current_version(db: Session, job_id: str) -> Optional[TranscriptVersion]:
        """Get the current version of a transcript."""
        return db.query(TranscriptVersion).filter(
            and_(TranscriptVersion.job_id == job_id, TranscriptVersion.is_current == True)
        ).first()
    
    @staticmethod
    def restore_version(db: Session, job_id: str, version_number: int, restored_by: Optional[str] = None) -> TranscriptVersion:
        """Restore a previous version as the current version."""
        
        # Get the version to restore
        version_to_restore = db.query(TranscriptVersion).filter(
            and_(
                TranscriptVersion.job_id == job_id,
                TranscriptVersion.version_number == version_number
            )
        ).first()
        
        if not version_to_restore:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Create new version with the restored content
        return TranscriptVersioningService.create_version(
            db=db,
            job_id=job_id,
            content=version_to_restore.content,
            created_by=restored_by,
            change_summary=f"Restored from version {version_number}"
        )


class TranscriptTagService:
    """Service for transcript tagging and organization."""
    
    @staticmethod
    def create_tag(db: Session, name: str, color: str = "#3B82F6", created_by: Optional[str] = None) -> TranscriptTag:
        """Create a new tag."""
        
        # Check if tag already exists
        existing_tag = db.query(TranscriptTag).filter(TranscriptTag.name == name).first()
        if existing_tag:
            raise HTTPException(status_code=400, detail="Tag already exists")
        
        tag = TranscriptTag(name=name, color=color, created_by=created_by)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        
        logger.info(f"Created tag '{name}' with color {color}")
        return tag
    
    @staticmethod
    def get_tags(db: Session) -> List[TranscriptTag]:
        """Get all available tags."""
        return db.query(TranscriptTag).order_by(TranscriptTag.name).all()
    
    @staticmethod
    def assign_tag(db: Session, job_id: str, tag_id: int, assigned_by: Optional[str] = None) -> JobTag:
        """Assign a tag to a job."""
        
        # Check if already assigned
        existing = db.query(JobTag).filter(
            and_(JobTag.job_id == job_id, JobTag.tag_id == tag_id)
        ).first()
        
        if existing:
            return existing
        
        job_tag = JobTag(job_id=job_id, tag_id=tag_id, assigned_by=assigned_by)
        db.add(job_tag)
        db.commit()
        
        logger.info(f"Assigned tag {tag_id} to job {job_id}")
        return job_tag
    
    @staticmethod
    def remove_tag(db: Session, job_id: str, tag_id: int) -> bool:
        """Remove a tag from a job."""
        
        job_tag = db.query(JobTag).filter(
            and_(JobTag.job_id == job_id, JobTag.tag_id == tag_id)
        ).first()
        
        if job_tag:
            db.delete(job_tag)
            db.commit()
            logger.info(f"Removed tag {tag_id} from job {job_id}")
            return True
        
        return False
    
    @staticmethod
    def get_job_tags(db: Session, job_id: str) -> List[TranscriptTag]:
        """Get all tags for a specific job."""
        return db.query(TranscriptTag).join(JobTag).filter(JobTag.job_id == job_id).all()


class TranscriptBookmarkService:
    """Service for transcript bookmarks and annotations."""
    
    @staticmethod
    def create_bookmark(
        db: Session,
        job_id: str,
        timestamp: float,
        title: str,
        note: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> TranscriptBookmark:
        """Create a bookmark for a specific timestamp."""
        
        bookmark = TranscriptBookmark(
            job_id=job_id,
            timestamp=timestamp,
            title=title,
            note=note,
            created_by=created_by
        )
        
        db.add(bookmark)
        db.commit()
        db.refresh(bookmark)
        
        logger.info(f"Created bookmark for job {job_id} at {timestamp}s")
        return bookmark
    
    @staticmethod
    def get_bookmarks(db: Session, job_id: str) -> List[TranscriptBookmark]:
        """Get all bookmarks for a job."""
        return db.query(TranscriptBookmark).filter(
            TranscriptBookmark.job_id == job_id
        ).order_by(TranscriptBookmark.timestamp).all()
    
    @staticmethod
    def update_bookmark(
        db: Session,
        bookmark_id: int,
        title: Optional[str] = None,
        note: Optional[str] = None
    ) -> TranscriptBookmark:
        """Update an existing bookmark."""
        
        bookmark = db.query(TranscriptBookmark).filter(TranscriptBookmark.id == bookmark_id).first()
        if not bookmark:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        
        if title is not None:
            bookmark.title = title
        if note is not None:
            bookmark.note = note
        
        db.commit()
        db.refresh(bookmark)
        
        return bookmark
    
    @staticmethod
    def delete_bookmark(db: Session, bookmark_id: int) -> bool:
        """Delete a bookmark."""
        
        bookmark = db.query(TranscriptBookmark).filter(TranscriptBookmark.id == bookmark_id).first()
        if bookmark:
            db.delete(bookmark)
            db.commit()
            logger.info(f"Deleted bookmark {bookmark_id}")
            return True
        
        return False


class BatchOperationService:
    """Service for batch operations on multiple transcripts."""
    
    @staticmethod
    def create_batch_operation(
        db: Session,
        operation_type: str,
        job_ids: List[str],
        parameters: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> BatchOperation:
        """Create a new batch operation."""
        
        operation_id = str(uuid.uuid4())
        
        operation = BatchOperation(
            id=operation_id,
            operation_type=operation_type,
            job_ids=job_ids,
            parameters=parameters or {},
            created_by=created_by
        )
        
        db.add(operation)
        db.commit()
        db.refresh(operation)
        
        logger.info(f"Created batch operation {operation_id} of type {operation_type} for {len(job_ids)} jobs")
        return operation
    
    @staticmethod
    def get_batch_operations(db: Session, created_by: Optional[str] = None) -> List[BatchOperation]:
        """Get batch operations, optionally filtered by creator."""
        
        query = db.query(BatchOperation)
        if created_by:
            query = query.filter(BatchOperation.created_by == created_by)
        
        return query.order_by(desc(BatchOperation.created_at)).all()
    
    @staticmethod
    def update_batch_status(
        db: Session,
        operation_id: str,
        status: str,
        result_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> BatchOperation:
        """Update the status of a batch operation."""
        
        operation = db.query(BatchOperation).filter(BatchOperation.id == operation_id).first()
        if not operation:
            raise HTTPException(status_code=404, detail="Batch operation not found")
        
        operation.status = status
        if result_data:
            operation.result_data = result_data
        if error_message:
            operation.error_message = error_message
        
        if status == "processing" and not operation.started_at:
            operation.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            operation.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(operation)
        
        return operation


class TranscriptExportService:
    """Service for exporting transcripts in various formats."""
    
    SUPPORTED_FORMATS = ["srt", "vtt", "docx", "pdf", "json", "txt"]
    
    @staticmethod
    def create_export(
        db: Session,
        job_ids: List[str],
        export_format: str,
        export_options: Optional[Dict] = None,
        created_by: Optional[str] = None
    ) -> TranscriptExport:
        """Create a new export operation."""
        
        if export_format not in TranscriptExportService.SUPPORTED_FORMATS:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {export_format}")
        
        export_id = str(uuid.uuid4())
        
        export = TranscriptExport(
            id=export_id,
            job_ids=job_ids,
            export_format=export_format,
            export_options=export_options or {},
            created_by=created_by,
            expires_at=datetime.utcnow() + timedelta(days=7)  # Auto-cleanup after 7 days
        )
        
        db.add(export)
        db.commit()
        db.refresh(export)
        
        logger.info(f"Created export {export_id} for {len(job_ids)} jobs in {export_format} format")
        return export
    
    @staticmethod
    def get_exports(db: Session, created_by: Optional[str] = None) -> List[TranscriptExport]:
        """Get export operations, optionally filtered by creator."""
        
        query = db.query(TranscriptExport).filter(
            or_(
                TranscriptExport.expires_at.is_(None),
                TranscriptExport.expires_at > datetime.utcnow()
            )
        )
        
        if created_by:
            query = query.filter(TranscriptExport.created_by == created_by)
        
        return query.order_by(desc(TranscriptExport.created_at)).all()
    
    @staticmethod
    def increment_download_count(db: Session, export_id: str) -> TranscriptExport:
        """Increment the download count for an export."""
        
        export = db.query(TranscriptExport).filter(TranscriptExport.id == export_id).first()
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        export.download_count += 1
        db.commit()
        db.refresh(export)
        
        return export