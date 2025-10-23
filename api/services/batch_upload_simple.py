"""
T020: Batch Upload Service - Add batch upload capabilities
Simplified service for handling multiple file uploads with progress tracking
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import tempfile
import shutil
from fastapi import UploadFile, HTTPException

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api.models import Job, JobStatusEnum
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
    allowed_formats: List[str] = None
    whisper_model: str = "base"
    language: Optional[str] = None
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
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class BatchUploadInfo:
    """Information about batch upload"""
    batch_id: str
    status: BatchUploadStatus
    total_files: int
    completed_files: int = 0
    failed_files: int = 0
    total_size: int = 0
    progress: float = 0.0
    jobs: Optional[List[BatchJobInfo]] = None
    created_at: Optional[datetime] = None
    config: Optional[BatchUploadConfig] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.jobs is None:
            self.jobs = []
    
    @property
    def is_active(self) -> bool:
        return self.status in [BatchUploadStatus.PENDING, BatchUploadStatus.PROCESSING]
    
    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100


class BatchUploadService:
    """Simplified service for managing batch uploads"""
    
    def __init__(self):
        self.active_batches: Dict[str, BatchUploadInfo] = {}
        self._batch_storage: Dict[str, Dict] = {}  # In-memory storage for demo
    
    async def create_batch_upload(
        self,
        files: List[UploadFile],
        config: Optional[BatchUploadConfig] = None
    ) -> str:
        """Create a new batch upload"""
        if config is None:
            config = BatchUploadConfig()
        
        # Validate batch constraints
        self._validate_batch_files(files, config)
        
        # Create batch ID and info
        batch_id = str(uuid.uuid4())
        total_size = sum((file.size or 0) for file in files)
        
        batch_info = BatchUploadInfo(
            batch_id=batch_id,
            status=BatchUploadStatus.PENDING,
            total_files=len(files),
            total_size=total_size,
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
        self._batch_storage[batch_id] = {
            "info": batch_info,
            "files": files
        }
        
        logger.info(f"Created batch upload {batch_id} with {len(files)} files")
        return batch_id
    
    async def start_batch_processing(self, batch_id: str) -> None:
        """Start processing a batch upload"""
        if batch_id not in self.active_batches:
            raise HTTPException(status_code=404, detail="Batch upload not found")
        
        batch_info = self.active_batches[batch_id]
        if batch_info.status != BatchUploadStatus.PENDING:
            raise HTTPException(status_code=400, detail="Batch already started or completed")
        
        # Update batch status
        batch_info.status = BatchUploadStatus.PROCESSING
        
        # Start background processing
        asyncio.create_task(self._process_batch_files(batch_id))
        
        logger.info(f"Started processing batch {batch_id}")
    
    async def _process_batch_files(self, batch_id: str) -> None:
        """Process all files in a batch"""
        try:
            batch_data = self._batch_storage.get(batch_id)
            if not batch_data:
                logger.error(f"Batch {batch_id} data not found")
                return
            
            batch_info = batch_data["info"]
            files = batch_data["files"]
            
            # Process files sequentially for simplicity
            for file, job_info in zip(files, batch_info.jobs):
                try:
                    await self._process_single_file(batch_id, job_info, file)
                except Exception as e:
                    logger.error(f"Error processing file {job_info.filename}: {e}")
                    job_info.status = BatchJobStatus.FAILED
                    job_info.error_message = str(e)
                    batch_info.failed_files += 1
                
                self._update_batch_progress(batch_info)
            
            # Update final batch status
            batch_info.status = BatchUploadStatus.COMPLETED
            batch_info.progress = 100.0
            
            logger.info(f"Completed processing batch {batch_id}")
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_id}: {e}")
            batch_info = self.active_batches.get(batch_id)
            if batch_info:
                batch_info.status = BatchUploadStatus.FAILED
    
    async def _process_single_file(
        self,
        batch_id: str,
        job_info: BatchJobInfo,
        file: UploadFile
    ) -> None:
        """Process a single file in the batch"""
        job_info.status = BatchJobStatus.PROCESSING
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(job_info.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Validate file (basic check)
            if not self._is_valid_audio_file(job_info.filename):
                raise ValueError("Invalid audio file format")
            
            # Create job in database
            with SessionLocal() as db:
                job = Job(
                    id=job_info.job_id,
                    original_filename=job_info.filename,
                    file_path=temp_path,
                    status="pending",
                    whisper_model=getattr(job_info, 'whisper_model', 'base'),
                    batch_id=batch_id
                )
                db.add(job)
                db.commit()
            
            # Simulate processing (replace with actual Whisper integration)
            await asyncio.sleep(0.1)  # Simulate work
            
            # Update job as completed
            with SessionLocal() as db:
                job = db.query(Job).filter(Job.id == job_info.job_id).first()
                if job:
                    job.status = "completed"
                    job.transcript_content = f"Simulated transcript for {job_info.filename}"
                    job.completed_at = datetime.utcnow()
                    db.commit()
            
            job_info.status = BatchJobStatus.COMPLETED
            job_info.progress = 100.0
            
        except Exception as e:
            logger.error(f"Error processing job {job_info.job_id}: {e}")
            job_info.status = BatchJobStatus.FAILED
            job_info.error_message = str(e)
            raise
        
        finally:
            # Cleanup temp file
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Could not cleanup temp file {temp_path}: {e}")
    
    def _is_valid_audio_file(self, filename: str) -> bool:
        """Basic audio file validation"""
        if not filename:
            return False
        
        valid_extensions = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".mp4"]
        file_ext = Path(filename).suffix.lower()
        return file_ext in valid_extensions
    
    def get_batch_info(self, batch_id: str) -> Optional[BatchUploadInfo]:
        """Get batch upload information"""
        return self.active_batches.get(batch_id)
    
    def get_batch_progress(self, batch_id: str) -> Dict:
        """Get batch upload progress"""
        batch_info = self.get_batch_info(batch_id)
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
    
    def cancel_batch_upload(self, batch_id: str) -> bool:
        """Cancel a batch upload"""
        batch_info = self.get_batch_info(batch_id)
        if not batch_info or not batch_info.is_active:
            return False
        
        batch_info.status = BatchUploadStatus.CANCELLED
        
        # Cancel pending jobs
        for job_info in batch_info.jobs:
            if job_info.status == BatchJobStatus.QUEUED:
                job_info.status = BatchJobStatus.SKIPPED
        
        logger.info(f"Cancelled batch upload {batch_id}")
        return True
    
    def list_batch_uploads(self, limit: int = 50) -> Dict:
        """List recent batch uploads"""
        batches = list(self.active_batches.values())
        batches.sort(key=lambda x: x.created_at, reverse=True)
        batches = batches[:limit]
        
        batch_summaries = []
        for batch_info in batches:
            batch_summaries.append({
                "batch_id": batch_info.batch_id,
                "status": batch_info.status,
                "total_files": batch_info.total_files,
                "completed_files": batch_info.completed_files,
                "failed_files": batch_info.failed_files,
                "progress": batch_info.progress,
                "created_at": batch_info.created_at.isoformat() if batch_info.created_at else None,
                "success_rate": batch_info.success_rate
            })
        
        return {
            "batches": batch_summaries,
            "total": len(self.active_batches)
        }
    
    def _validate_batch_files(
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
        
        total_size = sum((file.size or 0) for file in files)
        if total_size > config.max_total_size:
            raise HTTPException(
                status_code=400,
                detail=f"Total file size too large. Maximum {config.max_total_size} bytes allowed"
            )
        
        for file in files:
            if (file.size or 0) > config.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} too large. Maximum {config.max_file_size} bytes per file"
                )
            
            # Check file extension
            if file.filename:
                file_ext = Path(file.filename).suffix.lower().lstrip('.')
                if file_ext not in config.allowed_formats:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {file.filename} has unsupported format. Allowed: {config.allowed_formats}"
                    )
    
    def _update_batch_progress(self, batch_info: BatchUploadInfo) -> None:
        """Update batch progress based on job statuses"""
        completed_jobs = sum(1 for job in batch_info.jobs if job.status == BatchJobStatus.COMPLETED)
        failed_jobs = sum(1 for job in batch_info.jobs if job.status == BatchJobStatus.FAILED)
        
        batch_info.completed_files = completed_jobs
        batch_info.failed_files = failed_jobs
        
        # Calculate progress
        total_processed = completed_jobs + failed_jobs
        batch_info.progress = (total_processed / batch_info.total_files) * 100 if batch_info.total_files > 0 else 0