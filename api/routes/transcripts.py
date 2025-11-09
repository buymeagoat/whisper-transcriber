"""Secure transcript retrieval routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.routes.dependencies import get_authenticated_user_id
from api.services.consolidated_transcript_service import transcript_service
from api.utils.logger import get_system_logger

logger = get_system_logger("transcripts_api")

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.get("/{job_id}")
async def read_transcript(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
) -> Dict[str, Any]:
    """Return transcript metadata and content for the authenticated user."""
    transcript = await transcript_service.get_transcript(job_id=job_id, user_id=user_id, db=db)
    if "transcript" not in transcript:
        # Surface a consistent error for callers expecting text once the job completes.
        raise HTTPException(status_code=404, detail="Transcript not available")
    return transcript


@router.get("/{job_id}/download")
async def download_transcript(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
):
    """Stream the transcript file after enforcing ownership checks."""
    transcript_path = await transcript_service.get_transcript_path(job_id=job_id, user_id=user_id, db=db)

    logger.info("User %s downloading transcript %s", user_id, job_id)
    return FileResponse(
        transcript_path,
        media_type="text/plain",
        filename=transcript_path.name,
    )


@router.get("/{job_id}/raw")
async def read_transcript_text(
    job_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_authenticated_user_id),
) -> PlainTextResponse:
    """Return only the transcript text, primarily for legacy clients."""
    transcript = await transcript_service.get_transcript(job_id=job_id, user_id=user_id, db=db)
    if "transcript" not in transcript:
        raise HTTPException(status_code=404, detail="Transcript not available")
    return PlainTextResponse(transcript["transcript"], media_type="text/plain; charset=utf-8")
