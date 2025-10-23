"""
Chunked Upload API Routes for T025 Phase 5: File Upload Optimization

Provides REST endpoints for chunked file upload operations with
parallel processing, resumable uploads, and real-time progress tracking.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile
from pydantic import BaseModel, Field
from api.services.chunked_upload_service import chunked_upload_service
from api.utils.logger import get_system_logger

logger = get_system_logger("chunked_upload_api")

router = APIRouter(prefix="/uploads", tags=["chunked-uploads"])


class InitializeUploadRequest(BaseModel):
    """Request model for initializing upload."""
    filename: str = Field(..., max_length=255, description="Original filename")
    file_size: int = Field(..., gt=0, description="Total file size in bytes")
    file_hash: Optional[str] = Field(None, description="Optional SHA256 hash for verification")
    model_name: str = Field(default="small", description="Whisper model to use")
    language: Optional[str] = Field(None, description="Optional language code")


class ChunkUploadResponse(BaseModel):
    """Response model for chunk upload."""
    chunk_number: int
    status: str
    chunk_hash: Optional[str] = None
    uploaded_chunks: int
    total_chunks: int
    progress_percent: float


class UploadStatusResponse(BaseModel):
    """Response model for upload status."""
    session_id: str
    status: str
    uploaded_chunks: int
    total_chunks: int
    progress_percent: float
    missing_chunks: list[int]
    expires_at: str
    original_filename: str


class FinalizeUploadResponse(BaseModel):
    """Response model for upload finalization."""
    status: str
    job_id: Optional[str] = None
    file_hash: Optional[str] = None
    final_filename: Optional[str] = None
    missing_chunks: Optional[list[int]] = None


# TODO: Replace with proper authentication when available
async def get_current_user_id(request: Request) -> str:
    """Get current user ID. Replace with proper auth integration."""
    # For development, extract from headers or use default
    user_id = request.headers.get("X-User-ID", "default-user")
    return user_id


@router.post("/initialize", response_model=Dict[str, Any])
async def initialize_upload(
    request: InitializeUploadRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Initialize a new chunked upload session."""
    try:
        result = await chunked_upload_service.initialize_upload(
            user_id=user_id,
            filename=request.filename,
            file_size=request.file_size,
            file_hash=request.file_hash,
            model_name=request.model_name,
            language=request.language
        )
        
        logger.info(f"Initialized upload session for user {user_id}: {request.filename}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to initialize upload: {e}")
        raise


@router.post("/{session_id}/chunks/{chunk_number}", response_model=ChunkUploadResponse)
async def upload_chunk(
    session_id: str,
    chunk_number: int,
    chunk_data: UploadFile = File(..., description="Chunk data"),
    user_id: str = Depends(get_current_user_id)
):
    """Upload a single chunk for a session."""
    try:
        # Validate chunk number
        if chunk_number < 0:
            raise HTTPException(status_code=400, detail="Invalid chunk number")
        
        # Read chunk data
        data = await chunk_data.read()
        
        if len(data) == 0:
            raise HTTPException(status_code=400, detail="Empty chunk data")
        
        result = await chunked_upload_service.upload_chunk(
            session_id=session_id,
            chunk_number=chunk_number,
            chunk_data=data,
            user_id=user_id
        )
        
        logger.debug(f"Uploaded chunk {chunk_number} for session {session_id}")
        return ChunkUploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload chunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/finalize", response_model=FinalizeUploadResponse)
async def finalize_upload(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Finalize upload by assembling chunks into final file."""
    try:
        result = await chunked_upload_service.finalize_upload(
            session_id=session_id,
            user_id=user_id
        )
        
        logger.info(f"Finalized upload for session {session_id}")
        return FinalizeUploadResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to finalize upload: {e}")
        raise


@router.get("/{session_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get current upload status and progress."""
    try:
        result = await chunked_upload_service.get_upload_status(
            session_id=session_id,
            user_id=user_id
        )
        
        return UploadStatusResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to get upload status: {e}")
        raise


@router.get("/{session_id}/resume", response_model=Dict[str, Any])
async def get_resume_info(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Get information needed to resume an interrupted upload."""
    try:
        status_result = await chunked_upload_service.get_upload_status(
            session_id=session_id,
            user_id=user_id
        )
        
        if status_result["status"] not in ["active"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot resume upload with status: {status_result['status']}"
            )
        
        return {
            "session_id": session_id,
            "missing_chunks": status_result["missing_chunks"],
            "uploaded_chunks": status_result["uploaded_chunks"],
            "total_chunks": status_result["total_chunks"],
            "resumable": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resume info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def cancel_upload(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Cancel an upload session and cleanup resources."""
    try:
        result = await chunked_upload_service.cancel_upload(
            session_id=session_id,
            user_id=user_id
        )
        
        logger.info(f"Cancelled upload session {session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to cancel upload: {e}")
        raise


@router.get("/", response_model=Dict[str, Any])
async def list_user_uploads(
    user_id: str = Depends(get_current_user_id),
    active_only: bool = False
):
    """List upload sessions for the current user."""
    try:
        # Get all sessions for user
        user_sessions = []
        
        for session_id, session in chunked_upload_service.sessions.items():
            if session.user_id == user_id:
                if active_only and session.status.value not in ["active", "assembling"]:
                    continue
                
                session_info = {
                    "session_id": session_id,
                    "original_filename": session.original_filename,
                    "status": session.status.value,
                    "uploaded_chunks": len(session.uploaded_chunks),
                    "total_chunks": session.total_chunks,
                    "progress_percent": round((len(session.uploaded_chunks) / session.total_chunks) * 100, 2),
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat()
                }
                user_sessions.append(session_info)
        
        return {
            "sessions": user_sessions,
            "total": len(user_sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to list user uploads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_upload_metrics():
    """Get upload service metrics."""
    try:
        metrics = chunked_upload_service.get_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get upload metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired_sessions():
    """Manually trigger cleanup of expired upload sessions."""
    try:
        await chunked_upload_service.cleanup_expired_sessions()
        return {"message": "Expired sessions cleanup completed"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
