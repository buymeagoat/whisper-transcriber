"""
User management routes for the Whisper Transcriber API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def list_users():
    """List users."""
    return {"users": []}
