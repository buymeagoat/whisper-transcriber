"""
User settings routes for the Whisper Transcriber API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/user-settings", tags=["user-settings"])

@router.get("/")
async def get_user_settings():
    """Get user settings."""
    return {"settings": {}}
