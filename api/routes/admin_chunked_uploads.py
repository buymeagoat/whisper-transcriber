"""
Admin Upload Monitoring Routes for T025 Phase 5: File Upload Optimization

Provides administrative endpoints for monitoring upload performance,
managing active upload sessions, and viewing system metrics.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from api.services.chunked_upload_service import chunked_upload_service, UploadStatus
from api.utils.logger import get_system_logger
import asyncio

logger = get_system_logger("admin_upload")

router = APIRouter(prefix="/admin/uploads", tags=["admin-uploads"])


class UploadSessionSummary(BaseModel):
    """Summary model for upload session."""
    session_id: str
    user_id: str
    original_filename: str
    status: str
    progress_percent: float
    uploaded_chunks: int
    total_chunks: int
    total_size: int
    created_at: str
    expires_at: str
    model_name: str
    language: Optional[str] = None


class UploadMetrics(BaseModel):
    """Model for upload system metrics."""
    total_sessions: int
    active_sessions: int
    assembling_sessions: int
    completed_sessions: int
    failed_sessions: int
    expired_sessions: int
    cancelled_sessions: int
    chunk_size: int
    max_parallel_chunks: int
    max_file_size: int
    storage_usage_mb: float
    active_uploads_by_user: Dict[str, int]


class BulkActionRequest(BaseModel):
    """Request model for bulk actions on sessions."""
    session_ids: List[str]
    action: str  # "cancel", "cleanup", "force_expire"


# TODO: Replace with proper admin authentication
async def verify_admin_access():
    """Verify admin access. Replace with proper auth integration."""
    # For development, allow all access
    # In production, check admin role/permissions
    return True


@router.get("/metrics", response_model=UploadMetrics)
async def get_upload_metrics(admin: bool = Depends(verify_admin_access)):
    """Get comprehensive upload system metrics."""
    try:
        base_metrics = chunked_upload_service.get_metrics()
        
        # Calculate additional metrics
        expired_sessions = sum(
            1 for s in chunked_upload_service.sessions.values() 
            if s.status == UploadStatus.EXPIRED
        )
        
        cancelled_sessions = sum(
            1 for s in chunked_upload_service.sessions.values() 
            if s.status == UploadStatus.CANCELLED
        )
        
        # Calculate storage usage
        storage_usage_bytes = 0
        for session_id in chunked_upload_service.sessions.keys():
            session_dir = chunked_upload_service._get_session_dir(session_id)
            if session_dir.exists():
                for file_path in session_dir.rglob("*"):
                    if file_path.is_file():
                        storage_usage_bytes += file_path.stat().st_size
        
        storage_usage_mb = storage_usage_bytes / (1024 * 1024)
        
        # Active uploads by user
        active_uploads_by_user = {}
        for session in chunked_upload_service.sessions.values():
            if session.status in [UploadStatus.ACTIVE, UploadStatus.ASSEMBLING]:
                user_id = session.user_id
                active_uploads_by_user[user_id] = active_uploads_by_user.get(user_id, 0) + 1
        
        return UploadMetrics(
            **base_metrics,
            expired_sessions=expired_sessions,
            cancelled_sessions=cancelled_sessions,
            storage_usage_mb=round(storage_usage_mb, 2),
            active_uploads_by_user=active_uploads_by_user
        )
        
    except Exception as e:
        logger.error(f"Failed to get upload metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=Dict[str, Any])
async def list_upload_sessions(
    admin: bool = Depends(verify_admin_access),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date"),
    limit: int = Query(100, description="Maximum number of sessions to return"),
    offset: int = Query(0, description="Number of sessions to skip")
):
    """List upload sessions with filtering options."""
    try:
        all_sessions = []
        
        for session_id, session in chunked_upload_service.sessions.items():
            # Apply filters
            if status and session.status.value != status:
                continue
            
            if user_id and session.user_id != user_id:
                continue
            
            if created_after and session.created_at < created_after:
                continue
            
            session_summary = UploadSessionSummary(
                session_id=session_id,
                user_id=session.user_id,
                original_filename=session.original_filename,
                status=session.status.value,
                progress_percent=round((len(session.uploaded_chunks) / session.total_chunks) * 100, 2),
                uploaded_chunks=len(session.uploaded_chunks),
                total_chunks=session.total_chunks,
                total_size=session.total_size,
                created_at=session.created_at.isoformat(),
                expires_at=session.expires_at.isoformat(),
                model_name=session.model_name,
                language=session.language
            )
            all_sessions.append(session_summary)
        
        # Sort by creation date (newest first)
        all_sessions.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        paginated_sessions = all_sessions[offset:offset + limit]
        
        return {
            "sessions": [session.dict() for session in paginated_sessions],
            "total": len(all_sessions),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to list upload sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_upload_session_details(
    session_id: str,
    admin: bool = Depends(verify_admin_access)
):
    """Get detailed information about a specific upload session."""
    try:
        session = await chunked_upload_service._load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        # Get chunk details
        session_dir = chunked_upload_service._get_session_dir(session_id)
        chunks_dir = session_dir / "chunks"
        
        chunk_details = []
        if chunks_dir.exists():
            for i in range(session.total_chunks):
                chunk_file = chunks_dir / f"chunk_{i:06d}.tmp"
                meta_file = chunks_dir / f"chunk_{i:06d}.meta"
                
                chunk_info = {
                    "chunk_number": i,
                    "uploaded": chunk_file.exists(),
                    "size": chunk_file.stat().st_size if chunk_file.exists() else 0,
                    "metadata": None
                }
                
                if meta_file.exists():
                    try:
                        import json
                        with open(meta_file, 'r') as f:
                            chunk_info["metadata"] = json.load(f)
                    except:
                        pass
                
                chunk_details.append(chunk_info)
        
        # Calculate storage usage
        storage_usage = 0
        if session_dir.exists():
            for file_path in session_dir.rglob("*"):
                if file_path.is_file():
                    storage_usage += file_path.stat().st_size
        
        return {
            "session": session.to_dict(),
            "chunk_details": chunk_details,
            "storage_usage_bytes": storage_usage,
            "storage_usage_mb": round(storage_usage / (1024 * 1024), 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/cancel")
async def admin_cancel_session(
    session_id: str,
    admin: bool = Depends(verify_admin_access)
):
    """Admin endpoint to cancel an upload session."""
    try:
        session = await chunked_upload_service._load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        # Cancel the session
        result = await chunked_upload_service.cancel_upload(session_id, session.user_id)
        
        logger.info(f"Admin cancelled upload session {session_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/force-expire")
async def admin_force_expire_session(
    session_id: str,
    admin: bool = Depends(verify_admin_access)
):
    """Admin endpoint to force expire an upload session."""
    try:
        session = await chunked_upload_service._load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Upload session not found")
        
        # Force expire the session
        session.status = UploadStatus.EXPIRED
        session.expires_at = datetime.utcnow()
        await chunked_upload_service._save_session(session)
        
        # Cleanup chunks
        await chunked_upload_service._cleanup_session_chunks(session_id)
        
        logger.info(f"Admin force-expired upload session {session_id}")
        return {"message": "Session force-expired successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to force-expire session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/expired")
async def cleanup_expired_sessions(admin: bool = Depends(verify_admin_access)):
    """Manually trigger cleanup of expired upload sessions."""
    try:
        await chunked_upload_service.cleanup_expired_sessions()
        
        logger.info("Admin triggered expired sessions cleanup")
        return {"message": "Expired sessions cleanup completed"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk-actions")
async def bulk_session_actions(
    request: BulkActionRequest,
    admin: bool = Depends(verify_admin_access)
):
    """Perform bulk actions on multiple upload sessions."""
    try:
        results = []
        
        for session_id in request.session_ids:
            try:
                if request.action == "cancel":
                    session = await chunked_upload_service._load_session(session_id)
                    if session:
                        await chunked_upload_service.cancel_upload(session_id, session.user_id)
                        results.append({"session_id": session_id, "status": "cancelled"})
                    else:
                        results.append({"session_id": session_id, "status": "not_found"})
                
                elif request.action == "cleanup":
                    await chunked_upload_service._cleanup_session_chunks(session_id)
                    results.append({"session_id": session_id, "status": "cleaned"})
                
                elif request.action == "force_expire":
                    session = await chunked_upload_service._load_session(session_id)
                    if session:
                        session.status = UploadStatus.EXPIRED
                        session.expires_at = datetime.utcnow()
                        await chunked_upload_service._save_session(session)
                        results.append({"session_id": session_id, "status": "expired"})
                    else:
                        results.append({"session_id": session_id, "status": "not_found"})
                
                else:
                    results.append({"session_id": session_id, "status": "invalid_action"})
                    
            except Exception as e:
                results.append({"session_id": session_id, "status": "error", "error": str(e)})
        
        logger.info(f"Admin bulk action '{request.action}' completed on {len(request.session_ids)} sessions")
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Failed to perform bulk actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/stats")
async def get_performance_stats(
    admin: bool = Depends(verify_admin_access),
    hours: int = Query(24, description="Number of hours to analyze")
):
    """Get upload performance statistics."""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Analyze sessions from the specified time period
        recent_sessions = [
            s for s in chunked_upload_service.sessions.values()
            if s.created_at >= cutoff_time
        ]
        
        if not recent_sessions:
            return {
                "period_hours": hours,
                "total_sessions": 0,
                "average_upload_time": None,
                "success_rate": 0,
                "average_file_size": 0,
                "most_used_models": {}
            }
        
        # Calculate statistics
        completed_sessions = [s for s in recent_sessions if s.status == UploadStatus.COMPLETED]
        failed_sessions = [s for s in recent_sessions if s.status == UploadStatus.FAILED]
        
        success_rate = len(completed_sessions) / len(recent_sessions) * 100
        average_file_size = sum(s.total_size for s in recent_sessions) / len(recent_sessions)
        
        # Model usage statistics
        model_usage = {}
        for session in recent_sessions:
            model = session.model_name
            model_usage[model] = model_usage.get(model, 0) + 1
        
        # Sort models by usage
        most_used_models = dict(sorted(model_usage.items(), key=lambda x: x[1], reverse=True))
        
        return {
            "period_hours": hours,
            "total_sessions": len(recent_sessions),
            "completed_sessions": len(completed_sessions),
            "failed_sessions": len(failed_sessions),
            "success_rate": round(success_rate, 2),
            "average_file_size_mb": round(average_file_size / (1024 * 1024), 2),
            "most_used_models": most_used_models
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage/usage")
async def get_storage_usage(admin: bool = Depends(verify_admin_access)):
    """Get detailed storage usage information."""
    try:
        uploads_dir = chunked_upload_service.uploads_dir
        sessions_dir = chunked_upload_service.sessions_dir
        
        # Calculate storage usage by category
        storage_usage = {
            "total_bytes": 0,
            "sessions_bytes": 0,
            "completed_files_bytes": 0,
            "temporary_chunks_bytes": 0,
            "breakdown_by_session": {}
        }
        
        # Calculate sessions storage
        if sessions_dir.exists():
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    session_usage = 0
                    chunks_usage = 0
                    
                    for file_path in session_dir.rglob("*"):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            session_usage += file_size
                            
                            if "chunks" in str(file_path):
                                chunks_usage += file_size
                    
                    storage_usage["breakdown_by_session"][session_dir.name] = {
                        "total_bytes": session_usage,
                        "chunks_bytes": chunks_usage
                    }
                    
                    storage_usage["sessions_bytes"] += session_usage
                    storage_usage["temporary_chunks_bytes"] += chunks_usage
        
        # Calculate completed files storage
        if uploads_dir.exists():
            for file_path in uploads_dir.iterdir():
                if file_path.is_file():
                    storage_usage["completed_files_bytes"] += file_path.stat().st_size
        
        storage_usage["total_bytes"] = (
            storage_usage["sessions_bytes"] + storage_usage["completed_files_bytes"]
        )
        
        # Convert to MB for readability
        return {
            "total_mb": round(storage_usage["total_bytes"] / (1024 * 1024), 2),
            "sessions_mb": round(storage_usage["sessions_bytes"] / (1024 * 1024), 2),
            "completed_files_mb": round(storage_usage["completed_files_bytes"] / (1024 * 1024), 2),
            "temporary_chunks_mb": round(storage_usage["temporary_chunks_bytes"] / (1024 * 1024), 2),
            "active_sessions": len([s for s in chunked_upload_service.sessions.values() 
                                  if s.status in [UploadStatus.ACTIVE, UploadStatus.ASSEMBLING]]),
            "cleanup_recommended": storage_usage["temporary_chunks_bytes"] > (100 * 1024 * 1024)  # >100MB
        }
        
    except Exception as e:
        logger.error(f"Failed to get storage usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
