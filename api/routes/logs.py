"""
Logs routes for the Whisper Transcriber API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/")
async def get_logs():
    """Get application logs."""
    return {"logs": []}
