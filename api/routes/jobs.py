"""
Job management routes for the Whisper Transcriber API.
Enhanced with cache invalidation for T025 Phase 2.
Enhanced with audit logging for T026 Security Hardening.
"""

# T026 Security: Fixed log injection vulnerability
from api.utils.log_sanitization import safe_log_format, sanitize_for_log

from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from api.orm_bootstrap import get_db
from api.models import Job, JobStatusEnum
from api.routes.dependencies import get_authenticated_user_id
from api.services.job_queue import job_queue
from api.settings import settings
from api.utils.logger import get_system_logger
from api.services.cache_hooks import job_cache_manager, cache_invalidator
import uuid
from datetime import datetime

# T026 Security Hardening - Audit logging integration
from api.audit.integration import (
    audit_data_operation,
    audit_administrative_action,
    extract_request_context
)
from api.audit.security_audit_logger import (
    AuditEventType,
    AuditSeverity,
    AuditOutcome
)

logger = get_system_logger("jobs_api")

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", response_model=Dict[str, Any])
async def create_job(
    request: Request,
    file: UploadFile = File(...),
    model: str = Form(default="small"),
    language: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Create a new transcription job."""
    try:
        # Extract user context for auditing
        user_context = extract_request_context(request)
        # Fall back to the authenticated header if the audit context is missing a user reference.
        user_id = user_context.get("user_id") or user_id
        
        # Validate file type - check both MIME type and file extension
        allowed_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac', '.webm']
        file_extension = Path(file.filename).suffix.lower() if file.filename else ""
        
        is_valid_mime = file.content_type in settings.allowed_file_types
        is_valid_extension = file_extension in allowed_extensions
        is_generic_binary = file.content_type == "application/octet-stream"
        
        # Allow if MIME type is valid OR if extension is valid (handles generic MIME types)
        if not (is_valid_mime or (is_generic_binary and is_valid_extension) or is_valid_extension):
            # Audit failed file upload
            audit_data_operation(
                user_id=user_id or "anonymous",
                action="upload",
                resource=safe_log_format("file:{}", sanitize_for_log(file.filename)),
                request=request,
                success=False
            )
            
            raise HTTPException(
                status_code=400,
                detail=safe_log_format("File type {} not allowed. Supported formats: {}", 
                                     sanitize_for_log(f"{file.content_type} (extension: {file_extension})"),
                                     sanitize_for_log(", ".join(allowed_extensions)))
            )
        
        # Validate file size
        content = await file.read()
        if len(content) > settings.max_file_size:
            # Audit failed file upload
            audit_data_operation(
                user_id=user_id or "anonymous",
                action="upload",
                resource=safe_log_format("file:{}", sanitize_for_log(file.filename)),
                request=request,
                success=False
            )
            
            raise HTTPException(
                status_code=400,
                detail=safe_log_format("File too large. Maximum size: {} bytes", sanitize_for_log(settings.max_file_size))
            )
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = settings.upload_dir / safe_log_format("{}_{}", sanitize_for_log(file_id), sanitize_for_log(file.filename))
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create job record
        job = Job(
            id=file_id,
            original_filename=file.filename,
            saved_filename=str(file_path),
            model=model,
            status=JobStatusEnum.QUEUED,
            user_id=user_id
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Submit to job queue
        queue_job_id = job_queue.submit_job(
            "transcribe_audio",
            audio_path=str(file_path),
            model=model,
            language=language,
            job_id=file_id
        )
        
        # Invalidate cache for job lists since a new job was created
        await job_cache_manager.job_created(file_id, {
            "status": job.status.value,
            "filename": file.filename,
            "model": model,
            "user_id": user_id
        })
        
        logger.info(safe_log_format("Created transcription job {} for file {}", sanitize_for_log(file_id), sanitize_for_log(file.filename)))
        
        return {
            "job_id": file_id,
            "status": job.status.value,
            "message": "Job created successfully",
            "queue_job_id": queue_job_id,
            "user_id": user_id
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors) without modification
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to create job: {}", sanitize_for_log(e)))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Get job status and details."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job or job.user_id != user_id:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get queue status if available
        try:
            queue_job = job_queue.get_job(job.id)
            queue_status = queue_job.state.lower() if queue_job else None
        except Exception:
            queue_status = None

        transcript_content = None
        transcript_download_url = None
        if getattr(job, "transcript_path", None):
            transcript_path = Path(job.transcript_path)
            try:
                if transcript_path.exists():
                    transcript_content = transcript_path.read_text(encoding="utf-8")
                    transcript_download_url = safe_log_format(
                        "/transcripts/{}/{}",
                        sanitize_for_log(job.id),
                        sanitize_for_log(transcript_path.name)
                    )
            except Exception as exc:
                logger.warning(
                    safe_log_format(
                        "Unable to read transcript for job {}: {}",
                        sanitize_for_log(job_id),
                        sanitize_for_log(exc)
                    )
                )

        return {
            "job_id": job.id,
            "original_filename": job.original_filename,
            "status": job.status.value,
            "queue_status": queue_status,
            "model_name": getattr(job, "model_name", getattr(job, "model", None)),
            "language": getattr(job, "language", None),
            "created_at": job.created_at.isoformat() if getattr(job, "created_at", None) else None,
            "completed_at": (
                getattr(job, "completed_at", None).isoformat()
                if getattr(job, "completed_at", None)
                else getattr(job, "finished_at", None).isoformat()
                if getattr(job, "finished_at", None)
                else None
            ),
            "transcript": transcript_content,
            "transcript_path": getattr(job, "transcript_path", None),
            "transcript_download_url": transcript_download_url,
            "error_message": getattr(job, "error_message", None)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job")

@router.get("/", response_model=Dict[str, Any])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """List all jobs."""
    jobs = (
        db.query(Job)
        .filter(Job.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    total = db.query(Job).filter(Job.user_id == user_id).count()
    
    return {
        "jobs": [
            {
                "job_id": job.id,
                "original_filename": job.original_filename,
                "status": job.status.value,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id)
):
    """Delete a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job or job.user_id != user_id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Cancel from queue if still pending
    job_queue.cancel_job(job_id)
    
    # Delete from database
    db.delete(job)
    db.commit()
    
    # Invalidate related caches
    await job_cache_manager.job_deleted(job_id)
    
    logger.info(safe_log_format("Deleted job {}", sanitize_for_log(job_id)))
    
    return {"message": "Job deleted successfully"}
    db.delete(job)
    db.commit()
    
    logger.info(safe_log_format("Deleted job {}", sanitize_for_log(job_id)))
    
    return {"message": "Job deleted successfully"}
