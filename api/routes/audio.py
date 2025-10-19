"""
Audio processing routes for the Whisper Transcriber API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/audio", tags=["audio"])

@router.get("/")
async def list_audio_files():
    """List audio files."""
    return {"files": []}
