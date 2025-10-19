"""
Text-to-speech routes for the Whisper Transcriber API.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post("/")
async def synthesize_speech():
    """Synthesize speech from text."""
    return {"message": "TTS not implemented"}
