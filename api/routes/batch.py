#!/usr/bin/env python3
"""
T027 Advanced Features: Batch Processing API Routes
API endpoints for batch upload and processing management.
"""

from typing import List, Optional
from datetime import datetime
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ValidationError

from api.orm_bootstrap import get_db
from api.utils.logger import get_system_logger
from api.services.auth_service import get_current_user
from api.services.batch_processor import (
    batch_processor, 
    BatchUploadRequest, 
    BatchInfo,
    BatchStatus,
    BatchJobPriority
)
from api.models import User

logger = get_system_logger("batch_routes")
router = APIRouter(prefix="/api/v1/batch", tags=["batch"])
security = HTTPBearer()

class BatchCreateResponse(BaseModel):
    """Response for batch creation."""
    batch_id: str
    message: str
    batch_info: BatchInfo

class BatchListResponse(BaseModel):
    """Response for batch listing."""
    batches: List[BatchInfo]
    total: int
    limit: int
    offset: int

class BatchProgressResponse(BaseModel):
    """Response for batch progress."""
    batch_id: str
    status: str
    progress_percentage: float
    processed_files: int
    total_files: int
    successful_files: int
    failed_files: int
    estimated_completion: Optional[datetime]

@router.post("/upload", response_model=BatchCreateResponse)
async def create_batch_upload(
    files: List[UploadFile] = File(..., description="Files to upload for batch processing"),
    batch_name: str = Form(..., description="Name for the batch"),
    description: Optional[str] = Form(None, description="Optional batch description"),
    model: str = Form("small", description="Whisper model to use"),
    language: Optional[str] = Form(None, description="Language code for transcription"),
    priority: str = Form(BatchJobPriority.NORMAL.value, description="Processing priority"),
    auto_start: bool = Form(True, description="Start processing immediately"),
    max_parallel_jobs: int = Form(3, description="Maximum parallel transcription jobs"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new batch upload with multiple files.
    
    This endpoint allows users to upload multiple audio files for batch transcription.
    Files are processed in parallel up to the specified limit.
    """
    
    try:
        # Validate request
        request = BatchUploadRequest(
            batch_name=batch_name,
            description=description,
            model=model,
            language=language,
            priority=priority,
            auto_start=auto_start,
            max_parallel_jobs=max_parallel_jobs
        )
        
        # Validate files
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one file is required"
            )
        
        # Check for valid audio files
        valid_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
        for file in files:
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All files must have valid filenames"
                )
            
            file_ext = file.filename.lower().split('.')[-1]
            if f'.{file_ext}' not in valid_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} has unsupported format. Supported: {', '.join(valid_extensions)}"
                )
        
        # Create batch
        batch_info = batch_processor.create_batch(
            db=db,
            user_id=current_user.id,
            files=files,
            request=request
        )
        
        logger.info(f"User {current_user.id} created batch {batch_info.batch_id} with {len(files)} files")
        
        return BatchCreateResponse(
            batch_id=batch_info.batch_id,
            message=f"Batch created successfully with {batch_info.total_files} files",
            batch_info=batch_info
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to create batch upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create batch upload"
        )

@router.get("/list", response_model=BatchListResponse)
async def list_user_batches(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    List all batches for the current user.
    
    Returns a paginated list of batch uploads with their current status.
    """
    
    try:
        batches = batch_processor.list_user_batches(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        return BatchListResponse(
            batches=batches,
            total=len(batches),  # Note: This is approximate for pagination
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to list batches for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve batch list"
        )

@router.get("/{batch_id}", response_model=BatchInfo)
async def get_batch_info(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific batch.
    
    Returns complete batch information including file-level details and progress.
    """
    
    try:
        batch_info = batch_processor.get_batch_info(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Check ownership
        if batch_info.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this batch"
            )
        
        return batch_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch info for {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve batch information"
        )

@router.get("/{batch_id}/progress", response_model=BatchProgressResponse)
async def get_batch_progress(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get current progress of a batch.
    
    Returns real-time progress information for batch processing.
    """
    
    try:
        batch_info = batch_processor.get_batch_info(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Check ownership
        if batch_info.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this batch"
            )
        
        return BatchProgressResponse(
            batch_id=batch_info.batch_id,
            status=batch_info.status,
            progress_percentage=batch_info.progress_percentage,
            processed_files=batch_info.processed_files,
            total_files=batch_info.total_files,
            successful_files=batch_info.successful_files,
            failed_files=batch_info.failed_files,
            estimated_completion=batch_info.estimated_completion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch progress for {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve batch progress"
        )

@router.post("/{batch_id}/start")
async def start_batch_processing(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start processing a batch that was created with auto_start=False.
    
    Initiates batch processing for all files in the batch.
    """
    
    try:
        batch_info = batch_processor.get_batch_info(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Check ownership
        if batch_info.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this batch"
            )
        
        # Check if batch can be started
        if batch_info.status != BatchStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch is in {batch_info.status} status and cannot be started"
            )
        
        # Start processing asynchronously
        asyncio.create_task(batch_processor.start_batch_processing(batch_id, db))
        
        logger.info(f"User {current_user.id} started batch processing for {batch_id}")
        
        return {
            "message": "Batch processing started",
            "batch_id": batch_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start batch processing for {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start batch processing"
        )

@router.post("/{batch_id}/cancel")
async def cancel_batch_processing(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a batch that is currently processing.
    
    Stops processing of remaining files in the batch.
    """
    
    try:
        batch_info = batch_processor.get_batch_info(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Check ownership
        if batch_info.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this batch"
            )
        
        # Check if batch can be cancelled
        if batch_info.status not in [BatchStatus.PENDING.value, BatchStatus.PROCESSING.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch is in {batch_info.status} status and cannot be cancelled"
            )
        
        # Cancel batch
        success = await batch_processor.cancel_batch(batch_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel batch"
            )
        
        logger.info(f"User {current_user.id} cancelled batch {batch_id}")
        
        return {
            "message": "Batch processing cancelled",
            "batch_id": batch_id,
            "status": "cancelled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel batch processing"
        )

@router.delete("/{batch_id}")
async def delete_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a batch and all its files.
    
    Permanently removes batch data and uploaded files.
    """
    
    try:
        batch_info = batch_processor.get_batch_info(batch_id)
        
        if not batch_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Check ownership
        if batch_info.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this batch"
            )
        
        # Check if batch can be deleted
        if batch_info.status == BatchStatus.PROCESSING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a batch that is currently processing. Cancel it first."
            )
        
        # Delete batch files
        import shutil
        from pathlib import Path
        
        batch_dir = Path(batch_processor.batch_storage_dir) / batch_id
        if batch_dir.exists():
            shutil.rmtree(batch_dir)
        
        # Remove from active batches
        if batch_id in batch_processor.active_batches:
            del batch_processor.active_batches[batch_id]
        
        if batch_id in batch_processor.processing_semaphores:
            del batch_processor.processing_semaphores[batch_id]
        
        logger.info(f"User {current_user.id} deleted batch {batch_id}")
        
        return {
            "message": "Batch deleted successfully",
            "batch_id": batch_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete batch {batch_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete batch"
        )

# Statistics endpoint
@router.get("/stats/summary")
async def get_batch_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get batch processing statistics for the current user.
    
    Returns summary statistics about user's batch processing activity.
    """
    
    try:
        batches = batch_processor.list_user_batches(
            user_id=current_user.id,
            limit=1000  # Get all batches for stats
        )
        
        stats = {
            "total_batches": len(batches),
            "active_batches": len([b for b in batches if b.status in [BatchStatus.PENDING.value, BatchStatus.PROCESSING.value]]),
            "completed_batches": len([b for b in batches if b.status == BatchStatus.COMPLETED.value]),
            "failed_batches": len([b for b in batches if b.status == BatchStatus.FAILED.value]),
            "cancelled_batches": len([b for b in batches if b.status == BatchStatus.CANCELLED.value]),
            "total_files_processed": sum(b.processed_files for b in batches),
            "total_files_successful": sum(b.successful_files for b in batches),
            "total_files_failed": sum(b.failed_files for b in batches),
            "success_rate": 0.0
        }
        
        # Calculate success rate
        total_processed = stats["total_files_processed"]
        if total_processed > 0:
            stats["success_rate"] = (stats["total_files_successful"] / total_processed) * 100
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get batch statistics for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve batch statistics"
        )