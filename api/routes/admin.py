"""
Admin routes for the Whisper Transcriber API.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from api.services.job_queue import job_queue
from api.orm_bootstrap import get_database_info
from api.settings import settings
from api.app_state import get_app_state
from api.utils.logger import get_system_logger

logger = get_system_logger("admin_api")

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats():
    """Get system statistics."""
    try:
        app_state = get_app_state()
        db_info = get_database_info()
        
        return {
            "app_state": app_state,
            "database": db_info,
            "settings": {
                "app_name": settings.app_name,
                "version": settings.version,
                "debug": settings.debug,
                "default_model": settings.default_model
            },
            "job_queue": {
                "total_jobs": len(job_queue.jobs),
                "active_jobs": len([j for j in job_queue.jobs.values() if j.status.value == "running"])
            }
        }
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def trigger_cleanup():
    """Trigger system cleanup."""
    try:
        job_queue.cleanup_old_jobs()
        return {"message": "Cleanup triggered successfully"}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "whisper-transcriber",
        "version": settings.version
    }
