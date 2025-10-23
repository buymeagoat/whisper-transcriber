"""
Metrics routes for the Whisper Transcriber API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/")
async def get_metrics():
    """Get system metrics."""
    return {"metrics": {}}
