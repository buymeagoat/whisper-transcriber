"""
T020: Batch Upload Service - Add batch upload capabilities
Service for handling multiple file uploads with progress tracking and queue management
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import os
from fastapi import UploadFile, HTTPException

from api.models import Job
from api.orm_bootstrap import SessionLocal
from api.settings import settings

logger = logging.getLogger(__name__)


class BatchUploadStatus(str, Enum):
    """Batch upload status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchJobStatus(str, Enum):
    """Individual job status in batch"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchUploadConfig:
    """Configuration for batch upload"""
    max_files: int = 50
    max_total_size: int = 5 * 1024 * 1024 * 1024  # 5GB
    max_file_size: int = 1024 * 1024 * 1024  # 1GB per file
    allowed_formats: Optional[List[str]] = None
    whisper_model: str = "base"
    language: Optional[str] = None
    include_timestamps: bool = True
    concurrent_jobs: int = 3
    
    def __post_init__(self):
        if self.allowed_formats is None:
            self.allowed_formats = ["mp3", "wav", "m4a", "flac", "ogg", "webm", "mp4"]


@dataclass
class BatchJobInfo:
    """Information about individual job in batch"""
    job_id: str
    filename: str
    file_size: int
    status: BatchJobStatus
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class BatchUploadInfo:
    """Information about batch upload"""
    batch_id: str
    status: BatchUploadStatus
    total_files: int
    completed_files: int
    failed_files: int
    total_size: int
    progress: float
    jobs: List[BatchJobInfo]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: Optional[BatchUploadConfig] = None
    
    @property
    def is_active(self) -> bool:
        return self.status in [BatchUploadStatus.PENDING, BatchUploadStatus.PROCESSING]
    
    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100


class BatchUploadService:
    """Service for managing batch uploads"""
    
    def __init__(self):
        self.active_batches: Dict[str, BatchUploadInfo] = {}
        self.processing_semaphore = asyncio.Semaphore(3)  # Default concurrent jobs
        
    async def create_batch_upload(
        self,
        files: List[UploadFile],
        config: Optional[BatchUploadConfig] = None
    ) -> str:
        """Create a new batch upload"""
        if config is None:
            config = BatchUploadConfig()
            
        # Validate batch constraints
        await self._validate_batch_files(files, config)
        
        # Create batch ID and info
        batch_id = str(uuid.uuid4())
        total_size = sum(file.size or 0 for file in files)
        batch_info = BatchUploadInfo(
            batch_id=batch_id,
            status=BatchUploadStatus.PENDING,
            total_files=len(files),
            completed_files=0,
            failed_files=0,
            total_size=total_size,
            progress=0.0,
            jobs=[],
            created_at=datetime.utcnow(),
            config=config
        )
        
        # Create job entries for each file
        for file in files:
            job_info = BatchJobInfo(
                job_id=str(uuid.uuid4()),
                filename=file.filename or f"file_{len(batch_info.jobs)}",
                file_size=file.size or 0,
                status=BatchJobStatus.QUEUED
            )
            batch_info.jobs.append(job_info)
        
        # Store batch info
        self.active_batches[batch_id] = batch_info
        
        # Cache batch info
        await self._cache_batch_info(batch_id, batch_info)
        
        logger.info(f"Created batch upload {batch_id} with {len(files)} files")
        return batch_id
    
    async def start_batch_processing(
        self,
        batch_id: str,
        files: List[UploadFile]
    ) -> None:
        """Start processing a batch upload"""
        batch_info = await self.get_batch_info(batch_id)
        if not batch_info:
            raise HTTPException(status_code=404, detail="Batch upload not found")
        
        if batch_info.status != BatchUploadStatus.PENDING:
            raise HTTPException(status_code=400, detail="Batch already started or completed")
        
        # Update batch status
        batch_info.status = BatchUploadStatus.PROCESSING
        batch_info.started_at = datetime.utcnow()
        await self._cache_batch_info(batch_id, batch_info)
        
        # Start background processing
        asyncio.create_task(self._process_batch_files(batch_id, files))
        
        logger.info(f"Started processing batch {batch_id}")
    
    async def _process_batch_files(
        self,
        batch_id: str,
        files: List[UploadFile]
    ) -> None:
        """Process all files in a batch"""
        try:
            batch_info = await self.get_batch_info(batch_id)
            if not batch_info:
                logger.error(f"Batch {batch_id} not found during processing")
                return
            
            # Create semaphore for concurrent processing
            semaphore = asyncio.Semaphore(batch_info.config.concurrent_jobs)
            
            # Process files concurrently
            tasks = []
            for i, (file, job_info) in enumerate(zip(files, batch_info.jobs)):
                task = asyncio.create_task(
                    self._process_single_file(batch_id, job_info, file, semaphore)
                )
                tasks.append(task)
            
            # Wait for all files to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update final batch status
            batch_info = await self.get_batch_info(batch_id)
            if batch_info:
                batch_info.status = BatchUploadStatus.COMPLETED
                batch_info.completed_at = datetime.utcnow()
                batch_info.progress = 100.0
                await self._cache_batch_info(batch_id, batch_info)
                
            logger.info(f"Completed processing batch {batch_id}")
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_id}: {e}")
            # Mark batch as failed
            batch_info = await self.get_batch_info(batch_id)
            if batch_info:
                batch_info.status = BatchUploadStatus.FAILED
                await self._cache_batch_info(batch_id, batch_info)
    
    async def _process_single_file(
        self,
        batch_id: str,
        job_info: BatchJobInfo,
        file: UploadFile,
        semaphore: asyncio.Semaphore
    ) -> None:
        """Process a single file in the batch"""
        async with semaphore:
            try:
                # Update job status
                job_info.status = BatchJobStatus.PROCESSING
                job_info.started_at = datetime.utcnow()
                await self._update_batch_progress(batch_id)
                
                # Save uploaded file temporarily
                temp_path = Path(settings.upload_path) / f"batch_{batch_id}_{job_info.job_id}_{file.filename}"
                async with aiofiles.open(temp_path, 'wb') as f:
                    content = await file.read()
                    await f.write(content)
                
                # Validate audio file
                file_info = await get_file_info(temp_path)
                if not validate_audio_file(temp_path):
                    raise ValueError("Invalid audio file format")
                
                # Create job in database
                job = Job(
                    id=job_info.job_id,
                    original_filename=file.filename,
                    file_path=str(temp_path),
                    status="pending",
                    whisper_model=job_info.config.whisper_model if hasattr(job_info, 'config') else "base",
                    language=job_info.config.language if hasattr(job_info, 'config') else None,
                    batch_id=batch_id
                )
                
                with db_session() as db:
                    db.add(job)
                    db.commit()
                    db.refresh(job)
                
                # Process with Whisper
                result = await self.whisper_service.transcribe_audio(
                    audio_path=temp_path,
                    model=job_info.config.whisper_model if hasattr(job_info, 'config') else "base",
                    language=job_info.config.language if hasattr(job_info, 'config') else None
                )
                
                # Update job with results
                with db_session() as db:
                    job = db.query(Job).filter(Job.id == job_info.job_id).first()
                    if job:
                        job.status = "completed"
                        job.transcript_content = result.get("text", "")
                        job.completed_at = datetime.utcnow()
                        db.commit()
                
                # Update job info
                job_info.status = BatchJobStatus.COMPLETED
                job_info.completed_at = datetime.utcnow()
                job_info.progress = 100.0
                
                # Cleanup temp file
                await aiofiles.os.remove(temp_path)
                
                logger.info(f"Completed job {job_info.job_id} in batch {batch_id}")
                
            except Exception as e:
                logger.error(f"Error processing job {job_info.job_id}: {e}")
                job_info.status = BatchJobStatus.FAILED
                job_info.error_message = str(e)
                
                # Update job in database
                try:
                    with db_session() as db:
                        job = db.query(Job).filter(Job.id == job_info.job_id).first()
                        if job:
                            job.status = "failed"
                            job.error_message = str(e)
                            db.commit()
                except Exception as db_error:
                    logger.error(f"Error updating failed job in database: {db_error}")
            
            finally:
                await self._update_batch_progress(batch_id)
    
    async def get_batch_info(self, batch_id: str) -> Optional[BatchUploadInfo]:
        """Get batch upload information"""
        # Try active batches first
        if batch_id in self.active_batches:
            return self.active_batches[batch_id]
        
        # Try cache
        cached = await cache.get(f"batch_upload:{batch_id}")
        if cached:
            return BatchUploadInfo(**cached)
        
        # Try database
        try:
            with db_session() as db:
                batch = db.query(BatchUpload).filter(BatchUpload.id == batch_id).first()
                if batch:
                    # Reconstruct batch info from database
                    jobs = db.query(Job).filter(Job.batch_id == batch_id).all()
                    job_infos = [
                        BatchJobInfo(
                            job_id=job.id,
                            filename=job.original_filename,
                            file_size=0,  # Size not stored in job
                            status=BatchJobStatus(job.status),
                            created_at=job.created_at,
                            completed_at=job.completed_at
                        )
                        for job in jobs
                    ]
                    
                    batch_info = BatchUploadInfo(
                        batch_id=batch_id,
                        status=BatchUploadStatus(batch.status),
                        total_files=len(jobs),
                        completed_files=len([j for j in jobs if j.status == "completed"]),
                        failed_files=len([j for j in jobs if j.status == "failed"]),
                        total_size=batch.total_size or 0,
                        progress=batch.progress or 0.0,
                        jobs=job_infos,
                        created_at=batch.created_at,
                        started_at=batch.started_at,
                        completed_at=batch.completed_at
                    )
                    
                    return batch_info
        except Exception as e:
            logger.error(f"Error retrieving batch from database: {e}")
        
        return None
    
    async def cancel_batch_upload(self, batch_id: str) -> bool:
        """Cancel a batch upload"""
        batch_info = await self.get_batch_info(batch_id)
        if not batch_info:
            return False
        
        if not batch_info.is_active:
            return False
        
        # Update status
        batch_info.status = BatchUploadStatus.CANCELLED
        await self._cache_batch_info(batch_id, batch_info)
        
        # Cancel pending jobs
        for job_info in batch_info.jobs:
            if job_info.status == BatchJobStatus.QUEUED:
                job_info.status = BatchJobStatus.SKIPPED
        
        logger.info(f"Cancelled batch upload {batch_id}")
        return True
    
    async def get_batch_progress(self, batch_id: str) -> Dict:
        """Get batch upload progress"""
        batch_info = await self.get_batch_info(batch_id)
        if not batch_info:
            raise HTTPException(status_code=404, detail="Batch upload not found")
        
        return {
            "batch_id": batch_id,
            "status": batch_info.status,
            "progress": batch_info.progress,
            "total_files": batch_info.total_files,
            "completed_files": batch_info.completed_files,
            "failed_files": batch_info.failed_files,
            "success_rate": batch_info.success_rate,
            "jobs": [
                {
                    "job_id": job.job_id,
                    "filename": job.filename,
                    "status": job.status,
                    "progress": job.progress,
                    "error_message": job.error_message
                }
                for job in batch_info.jobs
            ]
        }
    
    async def list_batch_uploads(
        self,
        status: Optional[BatchUploadStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """List batch uploads with pagination"""
        try:
            with db_session() as db:
                query = db.query(BatchUpload)
                
                if status:
                    query = query.filter(BatchUpload.status == status.value)
                
                query = query.order_by(BatchUpload.created_at.desc())
                total = query.count()
                batches = query.offset(offset).limit(limit).all()
                
                batch_summaries = []
                for batch in batches:
                    batch_info = await self.get_batch_info(batch.id)
                    if batch_info:
                        batch_summaries.append({
                            "batch_id": batch.id,
                            "status": batch_info.status,
                            "total_files": batch_info.total_files,
                            "completed_files": batch_info.completed_files,
                            "failed_files": batch_info.failed_files,
                            "progress": batch_info.progress,
                            "created_at": batch_info.created_at.isoformat(),
                            "success_rate": batch_info.success_rate
                        })
                
                return {
                    "batches": batch_summaries,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.error(f"Error listing batch uploads: {e}")
            return {"batches": [], "total": 0, "limit": limit, "offset": offset}
    
    async def _validate_batch_files(
        self,
        files: List[UploadFile],
        config: BatchUploadConfig
    ) -> None:
        """Validate batch upload files"""
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > config.max_files:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Maximum {config.max_files} files allowed"
            )
        
        total_size = sum(file.size for file in files)
        if total_size > config.max_total_size:
            raise HTTPException(
                status_code=400,
                detail=f"Total file size too large. Maximum {config.max_total_size} bytes allowed"
            )
        
        for file in files:
            if file.size > config.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} too large. Maximum {config.max_file_size} bytes per file"
                )
            
            # Check file extension
            file_ext = Path(file.filename).suffix.lower().lstrip('.')
            if file_ext not in config.allowed_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} has unsupported format. Allowed: {config.allowed_formats}"
                )
    
    async def _cache_batch_info(self, batch_id: str, batch_info: BatchUploadInfo) -> None:
        """Cache batch upload information"""
        try:
            cache_data = {
                "batch_id": batch_info.batch_id,
                "status": batch_info.status,
                "total_files": batch_info.total_files,
                "completed_files": batch_info.completed_files,
                "failed_files": batch_info.failed_files,
                "total_size": batch_info.total_size,
                "progress": batch_info.progress,
                "created_at": batch_info.created_at.isoformat(),
                "started_at": batch_info.started_at.isoformat() if batch_info.started_at else None,
                "completed_at": batch_info.completed_at.isoformat() if batch_info.completed_at else None,
                "jobs": [
                    {
                        "job_id": job.job_id,
                        "filename": job.filename,
                        "file_size": job.file_size,
                        "status": job.status,
                        "progress": job.progress,
                        "error_message": job.error_message,
                        "created_at": job.created_at.isoformat(),
                        "started_at": job.started_at.isoformat() if job.started_at else None,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None
                    }
                    for job in batch_info.jobs
                ]
            }
            
            # Cache for 1 hour for active batches, 24 hours for completed
            ttl = 3600 if batch_info.is_active else 86400
            await cache.set(f"batch_upload:{batch_id}", cache_data, expire=ttl)
            
        except Exception as e:
            logger.error(f"Error caching batch info: {e}")
    
    async def _update_batch_progress(self, batch_id: str) -> None:
        """Update batch progress based on job statuses"""
        batch_info = await self.get_batch_info(batch_id)
        if not batch_info:
            return
        
        # Count job statuses
        completed_jobs = sum(1 for job in batch_info.jobs if job.status == BatchJobStatus.COMPLETED)
        failed_jobs = sum(1 for job in batch_info.jobs if job.status == BatchJobStatus.FAILED)
        processing_jobs = sum(1 for job in batch_info.jobs if job.status == BatchJobStatus.PROCESSING)
        
        # Update counts
        batch_info.completed_files = completed_jobs
        batch_info.failed_files = failed_jobs
        
        # Calculate progress
        total_processed = completed_jobs + failed_jobs
        batch_info.progress = (total_processed / batch_info.total_files) * 100 if batch_info.total_files > 0 else 0
        
        # Update cache
        await self._cache_batch_info(batch_id, batch_info)
        
        logger.debug(f"Updated batch {batch_id} progress: {batch_info.progress:.1f}%")