"""
Progress tracking routes for the Whisper Transcriber API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/progress", tags=["progress"])

@router.get("/{job_id}")
async def get_progress(job_id: str):
    """Get job progress."""
    return {"job_id": job_id, "progress": 0}
