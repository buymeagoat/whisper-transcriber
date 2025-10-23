"""
T020: Batch Upload API Routes - Add batch upload capabilities
RESTful API endpoints for batch upload functionality
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from api.services.batch_upload_simple import (
    BatchUploadService, 
    BatchUploadConfig,
    BatchUploadStatus
)
# from api.middlewares.access_log import log_route_access  # Temporarily disabled

router = APIRouter(prefix="/batch-upload", tags=["batch-upload"])
batch_service = BatchUploadService()


# Request/Response Models
class BatchUploadRequest(BaseModel):
    """Request model for batch upload configuration"""
    max_files: int = Field(default=50, ge=1, le=100)
    max_file_size: int = Field(default=1024*1024*1024, ge=1)  # 1GB
    max_total_size: int = Field(default=5*1024*1024*1024, ge=1)  # 5GB
    whisper_model: str = Field(default="base")
    language: Optional[str] = None
    concurrent_jobs: int = Field(default=3, ge=1, le=10)


class BatchUploadResponse(BaseModel):
    """Response model for batch upload creation"""
    batch_id: str
    status: str
    total_files: int
    message: str


class BatchProgressResponse(BaseModel):
    """Response model for batch progress"""
    batch_id: str
    status: str
    progress: float
    total_files: int
    completed_files: int
    failed_files: int
    success_rate: float
    jobs: List[dict]


class BatchListResponse(BaseModel):
    """Response model for batch list"""
    batches: List[dict]
    total: int


@router.post("/create", response_model=BatchUploadResponse)
# @log_route_access  # Temporarily disabled
async def create_batch_upload(
    files: List[UploadFile] = File(...),
    config_json: str = Form(default='{}')
):
    """
    Create a new batch upload with multiple files
    """
    try:
        # Parse configuration if provided
        import json
        config_data = json.loads(config_json) if config_json else {}
        
        # Create configuration
        config = BatchUploadConfig(
            max_files=config_data.get('max_files', 50),
            max_file_size=config_data.get('max_file_size', 1024*1024*1024),
            max_total_size=config_data.get('max_total_size', 5*1024*1024*1024),
            whisper_model=config_data.get('whisper_model', 'base'),
            language=config_data.get('language'),
            concurrent_jobs=config_data.get('concurrent_jobs', 3)
        )
        
        # Create batch upload
        batch_id = await batch_service.create_batch_upload(files, config)
        
        return BatchUploadResponse(
            batch_id=batch_id,
            status="pending",
            total_files=len(files),
            message=f"Batch upload created successfully with {len(files)} files"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create batch upload: {str(e)}")


@router.post("/{batch_id}/start")
# @log_route_access  # Temporarily disabled
async def start_batch_processing(batch_id: str):
    """
    Start processing a batch upload
    """
    try:
        await batch_service.start_batch_processing(batch_id)
        
        return {
            "batch_id": batch_id,
            "status": "processing",
            "message": "Batch processing started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch processing: {str(e)}")


@router.get("/{batch_id}/progress", response_model=BatchProgressResponse)
# @log_route_access  # Temporarily disabled
async def get_batch_progress(batch_id: str):
    """
    Get the current progress of a batch upload
    """
    try:
        progress_data = batch_service.get_batch_progress(batch_id)
        
        return BatchProgressResponse(
            batch_id=progress_data["batch_id"],
            status=progress_data["status"],
            progress=progress_data["progress"],
            total_files=progress_data["total_files"],
            completed_files=progress_data["completed_files"],
            failed_files=progress_data["failed_files"],
            success_rate=progress_data["success_rate"],
            jobs=progress_data["jobs"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch progress: {str(e)}")


@router.get("/{batch_id}/status")
# @log_route_access  # Temporarily disabled
async def get_batch_status(batch_id: str):
    """
    Get basic status information for a batch upload
    """
    try:
        batch_info = batch_service.get_batch_info(batch_id)
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
            "created_at": batch_info.created_at.isoformat() if batch_info.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@router.post("/{batch_id}/cancel")
# @log_route_access  # Temporarily disabled
async def cancel_batch_upload(batch_id: str):
    """
    Cancel a batch upload
    """
    try:
        success = batch_service.cancel_batch_upload(batch_id)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Cannot cancel batch upload (not found or not active)"
            )
        
        return {
            "batch_id": batch_id,
            "status": "cancelled",
            "message": "Batch upload cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel batch upload: {str(e)}")


@router.get("/list", response_model=BatchListResponse)
# @log_route_access  # Temporarily disabled
async def list_batch_uploads(
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List batch uploads with optional status filtering
    """
    try:
        # Validate status if provided
        if status and status not in [s.value for s in BatchUploadStatus]:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        batch_data = batch_service.list_batch_uploads(limit=limit)
        
        # Filter by status if provided
        if status:
            batch_data["batches"] = [
                batch for batch in batch_data["batches"] 
                if batch["status"] == status
            ]
        
        return BatchListResponse(
            batches=batch_data["batches"],
            total=batch_data["total"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list batch uploads: {str(e)}")


@router.get("/{batch_id}/jobs")
# @log_route_access  # Temporarily disabled
async def get_batch_jobs(batch_id: str):
    """
    Get detailed information about jobs in a batch
    """
    try:
        batch_info = batch_service.get_batch_info(batch_id)
        if not batch_info:
            raise HTTPException(status_code=404, detail="Batch upload not found")
        
        jobs_data = []
        for job in batch_info.jobs:
            jobs_data.append({
                "job_id": job.job_id,
                "filename": job.filename,
                "file_size": job.file_size,
                "status": job.status,
                "progress": job.progress,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None
            })
        
        return {
            "batch_id": batch_id,
            "total_jobs": len(jobs_data),
            "jobs": jobs_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch jobs: {str(e)}")


@router.delete("/{batch_id}")
# @log_route_access  # Temporarily disabled
async def delete_batch_upload(batch_id: str):
    """
    Delete a completed or failed batch upload
    """
    try:
        batch_info = batch_service.get_batch_info(batch_id)
        if not batch_info:
            raise HTTPException(status_code=404, detail="Batch upload not found")
        
        if batch_info.is_active:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete active batch upload. Cancel it first."
            )
        
        # Remove from active batches (in a real implementation, also clean up database)
        if batch_id in batch_service.active_batches:
            del batch_service.active_batches[batch_id]
        if batch_id in batch_service._batch_storage:
            del batch_service._batch_storage[batch_id]
        
        return {
            "batch_id": batch_id,
            "message": "Batch upload deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete batch upload: {str(e)}")


@router.get("/stats")
# @log_route_access  # Temporarily disabled
async def get_batch_upload_stats():
    """
    Get statistics about batch uploads
    """
    try:
        all_batches = list(batch_service.active_batches.values())
        
        stats = {
            "total_batches": len(all_batches),
            "active_batches": len([b for b in all_batches if b.is_active]),
            "completed_batches": len([b for b in all_batches if b.status == BatchUploadStatus.COMPLETED]),
            "failed_batches": len([b for b in all_batches if b.status == BatchUploadStatus.FAILED]),
            "total_files_processed": sum(b.total_files for b in all_batches),
            "total_files_completed": sum(b.completed_files for b in all_batches),
            "total_files_failed": sum(b.failed_files for b in all_batches),
            "average_success_rate": sum(b.success_rate for b in all_batches) / len(all_batches) if all_batches else 0
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch upload stats: {str(e)}")