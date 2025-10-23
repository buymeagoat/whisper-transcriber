#!/usr/bin/env python3
"""
T027 Advanced Features: Batch Processing Service
Service for handling multiple file uploads and batch transcription processing.
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set
from enum import Enum
import json
import os
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from fastapi import UploadFile, HTTPException, status
from pydantic import BaseModel, Field

from api.orm_bootstrap import get_db
from api.models import Job, JobStatusEnum, User
from api.services.chunked_upload_service import chunked_upload_service
from api.app_state import handle_whisper
from api.paths import storage
from api.utils.logger import get_system_logger
from api.services.websocket_job_integration import get_job_notifier

logger = get_system_logger("batch_processor")

class BatchStatus(Enum):
    """Batch processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class BatchJobPriority(Enum):
    """Batch job priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class BatchUploadRequest(BaseModel):
    """Request model for batch upload."""
    batch_name: str = Field(..., min_length=1, max_length=255, description="Name for the batch")
    description: Optional[str] = Field(None, max_length=1000, description="Optional batch description")
    model: str = Field("small", description="Whisper model to use for all files")
    language: Optional[str] = Field(None, description="Language code for transcription")
    priority: str = Field(BatchJobPriority.NORMAL.value, description="Processing priority")
    auto_start: bool = Field(True, description="Start processing immediately")
    max_parallel_jobs: int = Field(3, ge=1, le=10, description="Maximum parallel transcription jobs")

class BatchFileInfo(BaseModel):
    """Information about a file in a batch."""
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    job_id: Optional[str] = None
    status: str = JobStatusEnum.QUEUED.value
    error_message: Optional[str] = None

class BatchInfo(BaseModel):
    """Batch processing information."""
    batch_id: str
    batch_name: str
    description: Optional[str]
    user_id: str
    status: str
    priority: str
    model: str
    language: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    max_parallel_jobs: int
    files: List[BatchFileInfo]
    progress_percentage: float
    estimated_completion: Optional[datetime]

class BatchProcessorService:
    """Service for batch processing of multiple files."""
    
    def __init__(self):
        self.active_batches: Dict[str, Dict[str, Any]] = {}
        self.processing_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.batch_storage_dir = Path(storage.UPLOAD_DIR) / "batches"
        self.batch_storage_dir.mkdir(exist_ok=True)
        
    def create_batch(
        self,
        db: Session,
        user_id: str,
        files: List[UploadFile],
        request: BatchUploadRequest
    ) -> BatchInfo:
        """Create a new batch upload."""
        
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one file is required for batch processing"
            )
        
        if len(files) > 50:  # Reasonable limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 files allowed per batch"
            )
        
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        
        # Create batch directory
        batch_dir = self.batch_storage_dir / batch_id
        batch_dir.mkdir(exist_ok=True)
        
        # Process and store files
        batch_files = []
        total_size = 0
        
        for file in files:
            # Validate file
            if not file.filename:
                continue
                
            # Check file size (100MB limit per file)
            file_size = 0
            content = file.file.read()
            file_size = len(content)
            file.file.seek(0)  # Reset file pointer
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} exceeds 100MB limit"
                )
            
            total_size += file_size
            
            # Generate unique filename
            file_ext = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = batch_dir / unique_filename
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Create file info
            file_info = BatchFileInfo(
                filename=unique_filename,
                original_filename=file.filename,
                file_size=file_size,
                content_type=file.content_type or "application/octet-stream",
                uploaded_at=datetime.utcnow()
            )
            
            batch_files.append(file_info)
        
        # Check total batch size (1GB limit)
        if total_size > 1024 * 1024 * 1024:  # 1GB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Total batch size exceeds 1GB limit"
            )
        
        # Create batch record
        batch_info = BatchInfo(
            batch_id=batch_id,
            batch_name=request.batch_name,
            description=request.description,
            user_id=user_id,
            status=BatchStatus.PENDING.value,
            priority=request.priority,
            model=request.model,
            language=request.language,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            total_files=len(batch_files),
            processed_files=0,
            successful_files=0,
            failed_files=0,
            max_parallel_jobs=request.max_parallel_jobs,
            files=batch_files,
            progress_percentage=0.0,
            estimated_completion=None
        )
        
        # Store batch metadata
        batch_metadata_path = batch_dir / "batch_info.json"
        with open(batch_metadata_path, "w") as f:
            json.dump(batch_info.dict(), f, default=str, indent=2)
        
        # Add to active batches
        self.active_batches[batch_id] = {
            "info": batch_info,
            "processing_jobs": set(),
            "completed_jobs": set(),
            "failed_jobs": set()
        }
        
        # Create semaphore for parallel processing
        self.processing_semaphores[batch_id] = asyncio.Semaphore(request.max_parallel_jobs)
        
        logger.info(f"Created batch {batch_id} with {len(batch_files)} files for user {user_id}")
        
        # Auto-start if requested
        if request.auto_start:
            asyncio.create_task(self.start_batch_processing(batch_id, db))
        
        return batch_info
    
    async def start_batch_processing(self, batch_id: str, db: Session):
        """Start processing a batch."""
        
        if batch_id not in self.active_batches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        batch_data = self.active_batches[batch_id]
        batch_info = batch_data["info"]
        
        if batch_info.status != BatchStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch is not in pending status"
            )
        
        # Update batch status
        batch_info.status = BatchStatus.PROCESSING.value
        batch_info.started_at = datetime.utcnow()
        
        # Estimate completion time (rough estimate: 2 minutes per file)
        estimated_duration = timedelta(minutes=2 * batch_info.total_files)
        batch_info.estimated_completion = batch_info.started_at + estimated_duration
        
        # Update metadata file
        await self._update_batch_metadata(batch_id)
        
        logger.info(f"Started batch processing for batch {batch_id}")
        
        # Create processing tasks for all files
        semaphore = self.processing_semaphores[batch_id]
        tasks = []
        
        for file_info in batch_info.files:
            task = asyncio.create_task(
                self._process_batch_file(batch_id, file_info, semaphore, db)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update final batch status
        await self._finalize_batch(batch_id)
    
    async def _process_batch_file(
        self,
        batch_id: str,
        file_info: BatchFileInfo,
        semaphore: asyncio.Semaphore,
        db: Session
    ):
        """Process a single file in the batch."""
        
        async with semaphore:
            try:
                batch_data = self.active_batches[batch_id]
                batch_info = batch_data["info"]
                
                # Create transcription job
                file_path = self.batch_storage_dir / batch_id / file_info.filename
                
                # Create job record in database
                job = Job(
                    id=str(uuid.uuid4()),
                    saved_filename=file_info.filename,
                    original_filename=file_info.original_filename,
                    model=batch_info.model,
                    language=batch_info.language,
                    status=JobStatusEnum.QUEUED,
                    user_id=batch_info.user_id,
                    created_at=datetime.utcnow(),
                    file_size=file_info.file_size
                )
                
                db.add(job)
                db.commit()
                db.refresh(job)
                
                # Update file info with job ID
                file_info.job_id = job.id
                file_info.status = JobStatusEnum.PROCESSING.value
                
                # Add to processing jobs
                batch_data["processing_jobs"].add(job.id)
                
                # Update batch metadata
                await self._update_batch_metadata(batch_id)
                
                # Start transcription
                job_dir = storage.TRANSCRIPTS_DIR / job.id
                job_dir.mkdir(exist_ok=True)
                
                # Process with Whisper
                await handle_whisper(
                    job.id,
                    str(file_path),
                    str(job_dir),
                    batch_info.model,
                    start_thread=False
                )
                
                # Update job status
                updated_job = db.query(Job).filter(Job.id == job.id).first()
                if updated_job:
                    file_info.status = updated_job.status.value
                    
                    if updated_job.status == JobStatusEnum.COMPLETED:
                        batch_data["completed_jobs"].add(job.id)
                        batch_data["processing_jobs"].discard(job.id)
                    elif updated_job.status == JobStatusEnum.FAILED:
                        batch_data["failed_jobs"].add(job.id)
                        batch_data["processing_jobs"].discard(job.id)
                        file_info.error_message = updated_job.error_message
                
                logger.info(f"Completed processing file {file_info.filename} in batch {batch_id}")
                
            except Exception as e:
                logger.error(f"Failed to process file {file_info.filename} in batch {batch_id}: {e}")
                
                # Update file as failed
                file_info.status = JobStatusEnum.FAILED.value
                file_info.error_message = str(e)
                
                batch_data["failed_jobs"].add(file_info.job_id)
                batch_data["processing_jobs"].discard(file_info.job_id)
            
            finally:
                # Update batch progress
                await self._update_batch_progress(batch_id)
    
    async def _update_batch_progress(self, batch_id: str):
        """Update batch processing progress."""
        
        if batch_id not in self.active_batches:
            return
        
        batch_data = self.active_batches[batch_id]
        batch_info = batch_data["info"]
        
        # Calculate progress
        completed = len(batch_data["completed_jobs"])
        failed = len(batch_data["failed_jobs"])
        processed = completed + failed
        
        batch_info.processed_files = processed
        batch_info.successful_files = completed
        batch_info.failed_files = failed
        batch_info.progress_percentage = (processed / batch_info.total_files) * 100
        
        # Update metadata
        await self._update_batch_metadata(batch_id)
        
        # Send WebSocket update
        try:
            job_notifier = await get_job_notifier()
            await job_notifier.broadcast_batch_update(batch_id, {
                "batch_id": batch_id,
                "status": batch_info.status,
                "progress_percentage": batch_info.progress_percentage,
                "processed_files": processed,
                "total_files": batch_info.total_files
            })
        except Exception as e:
            logger.warning(f"Failed to send batch progress update: {e}")
    
    async def _finalize_batch(self, batch_id: str):
        """Finalize batch processing."""
        
        if batch_id not in self.active_batches:
            return
        
        batch_data = self.active_batches[batch_id]
        batch_info = batch_data["info"]
        
        # Determine final status
        if batch_info.failed_files == 0:
            batch_info.status = BatchStatus.COMPLETED.value
        elif batch_info.successful_files == 0:
            batch_info.status = BatchStatus.FAILED.value
        else:
            batch_info.status = BatchStatus.COMPLETED.value  # Partial success
        
        batch_info.completed_at = datetime.utcnow()
        batch_info.progress_percentage = 100.0
        
        # Update metadata
        await self._update_batch_metadata(batch_id)
        
        logger.info(f"Finalized batch {batch_id}: {batch_info.successful_files}/{batch_info.total_files} successful")
    
    async def _update_batch_metadata(self, batch_id: str):
        """Update batch metadata file."""
        
        if batch_id not in self.active_batches:
            return
        
        batch_info = self.active_batches[batch_id]["info"]
        batch_metadata_path = self.batch_storage_dir / batch_id / "batch_info.json"
        
        try:
            with open(batch_metadata_path, "w") as f:
                json.dump(batch_info.dict(), f, default=str, indent=2)
        except Exception as e:
            logger.error(f"Failed to update batch metadata for {batch_id}: {e}")
    
    def get_batch_info(self, batch_id: str) -> Optional[BatchInfo]:
        """Get batch information."""
        
        if batch_id in self.active_batches:
            return self.active_batches[batch_id]["info"]
        
        # Try to load from disk
        batch_metadata_path = self.batch_storage_dir / batch_id / "batch_info.json"
        
        if batch_metadata_path.exists():
            try:
                with open(batch_metadata_path, "r") as f:
                    data = json.load(f)
                return BatchInfo(**data)
            except Exception as e:
                logger.error(f"Failed to load batch metadata for {batch_id}: {e}")
        
        return None
    
    def list_user_batches(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[BatchInfo]:
        """List batches for a user."""
        
        batches = []
        
        # Check active batches
        for batch_id, batch_data in self.active_batches.items():
            batch_info = batch_data["info"]
            if batch_info.user_id == user_id:
                batches.append(batch_info)
        
        # Check stored batches
        for batch_dir in self.batch_storage_dir.iterdir():
            if batch_dir.is_dir() and batch_dir.name not in self.active_batches:
                metadata_path = batch_dir / "batch_info.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r") as f:
                            data = json.load(f)
                        batch_info = BatchInfo(**data)
                        if batch_info.user_id == user_id:
                            batches.append(batch_info)
                    except Exception as e:
                        logger.warning(f"Failed to load batch {batch_dir.name}: {e}")
        
        # Sort by creation date (newest first)
        batches.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return batches[offset:offset + limit]
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch."""
        
        if batch_id not in self.active_batches:
            return False
        
        batch_data = self.active_batches[batch_id]
        batch_info = batch_data["info"]
        
        if batch_info.status not in [BatchStatus.PENDING.value, BatchStatus.PROCESSING.value]:
            return False
        
        # Update status
        batch_info.status = BatchStatus.CANCELLED.value
        batch_info.completed_at = datetime.utcnow()
        
        # Update metadata
        await self._update_batch_metadata(batch_id)
        
        logger.info(f"Cancelled batch {batch_id}")
        return True
    
    def cleanup_old_batches(self, days: int = 30):
        """Clean up old batch files."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cleaned_count = 0
        
        for batch_dir in self.batch_storage_dir.iterdir():
            if not batch_dir.is_dir():
                continue
            
            metadata_path = batch_dir / "batch_info.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r") as f:
                        data = json.load(f)
                    
                    created_at = datetime.fromisoformat(data.get("created_at", ""))
                    
                    if created_at < cutoff_date:
                        # Remove batch directory
                        import shutil
                        shutil.rmtree(batch_dir)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old batch {batch_dir.name}")
                        
                except Exception as e:
                    logger.warning(f"Failed to check batch {batch_dir.name}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old batches")
        return cleaned_count

# Create singleton instance
batch_processor = BatchProcessorService()