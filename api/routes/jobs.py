"""
Job management routes for the Whisper Transcriber API.
Enhanced with cache invalidation for T025 Phase 2.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from api.orm_bootstrap import get_db
from api.models import Job, JobStatusEnum
from api.services.job_queue import job_queue
from api.settings import settings
from api.utils.logger import get_system_logger
from api.services.cache_hooks import job_cache_manager, cache_invalidator
import uuid
from datetime import datetime

logger = get_system_logger("jobs_api")

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", response_model=Dict[str, Any])
async def create_job(
    file: UploadFile = File(...),
    model: str = Form(default="small"),
    language: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    """Create a new transcription job."""
    try:
        # Validate file type
        if file.content_type not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Validate file size
        content = await file.read()
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_file_size} bytes"
            )
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = settings.upload_dir / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create job record
        job = Job(
            id=file_id,
            original_filename=file.filename,
            file_path=str(file_path),
            model_name=model,
            language=language,
            status=JobStatusEnum.QUEUED
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
            "model": model
        })
        
        logger.info(f"Created transcription job {file_id} for file {file.filename}")
        
        return {
            "job_id": file_id,
            "status": job.status.value,
            "message": "Job created successfully",
            "queue_job_id": queue_job_id
        }
    
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job status and details."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get queue status if available
    queue_job = job_queue.get_job(job_id)
    queue_status = queue_job.status.value if queue_job else None
    
    return {
        "job_id": job.id,
        "original_filename": job.original_filename,
        "status": job.status.value,
        "queue_status": queue_status,
        "model_name": job.model_name,
        "language": job.language,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "transcript": job.transcript,
        "error_message": job.error_message
    }

@router.get("/", response_model=Dict[str, Any])
async def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all jobs."""
    jobs = db.query(Job).offset(skip).limit(limit).all()
    total = db.query(Job).count()
    
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
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Cancel from queue if still pending
    job_queue.cancel_job(job_id)
    
    # Delete from database
    db.delete(job)
    db.commit()
    
    # Invalidate related caches
    await job_cache_manager.job_deleted(job_id)
    
    logger.info(f"Deleted job {job_id}")
    
    return {"message": "Job deleted successfully"}
    db.delete(job)
    db.commit()
    
    logger.info(f"Deleted job {job_id}")
    
    return {"message": "Job deleted successfully"}
