"""
Consolidated Transcript Service

This service provides a unified interface for managing transcripts,
including retrieval, export, and search functionality.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiofiles

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from api.models import Job, JobStatusEnum
from api.settings import settings
from api.utils.logger import get_system_logger
from api.paths import storage

logger = get_system_logger("transcript_service")


class ConsolidatedTranscriptService:
    """Service for managing transcripts."""

    def __init__(self):
        """Initialize the transcript service."""
        self.transcript_dir = storage.transcripts_dir
        self.transcript_dir.mkdir(parents=True, exist_ok=True)

    async def get_transcript(
        self,
        job_id: str,
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Retrieve transcript for a specific job."""
        try:
            job = db.get(Job, job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            # Verify ownership
            if not job.user_id:
                raise HTTPException(status_code=403, detail="Transcript owner missing")

            if job.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Check if job is completed
            if job.status != JobStatusEnum.COMPLETED:
                return {
                    "job_id": job_id,
                    "status": job.status.value,
                    "message": "Transcription not yet complete"
                }

            # Get transcript path
            if not job.transcript_path:
                raise HTTPException(status_code=404, detail="Transcript not found")

            transcript_path = Path(job.transcript_path)
            if not transcript_path.exists():
                raise HTTPException(status_code=404, detail="Transcript file not found")

            # Read transcript
            async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
                transcript_text = await f.read()

            return {
                "job_id": job_id,
                "status": job.status.value,
                "transcript": transcript_text,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.finished_at.isoformat() if job.finished_at else None,
                "model": job.model,
                "language": getattr(job, "language", None),
                "original_filename": job.original_filename
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving transcript for job {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_transcripts(
        self,
        user_id: str,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of user's transcripts with pagination."""
        try:
            # Build query
            query = db.query(Job).filter(Job.user_id == user_id)
            
            if status:
                try:
                    status_enum = JobStatusEnum[status.upper()]
                    query = query.filter(Job.status == status_enum)
                except KeyError:
                    raise HTTPException(status_code=400, detail="Invalid status")

            # Get total count
            total_count = query.count()

            # Get paginated results
            jobs = query.order_by(Job.created_at.desc()) \
                       .offset(offset) \
                       .limit(limit) \
                       .all()

            results = []
            for job in jobs:
                job_data = {
                    "job_id": job.id,
                    "status": job.status.value,
                    "original_filename": job.original_filename,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.finished_at.isoformat() if job.finished_at else None,
                    "model": job.model,
                    "language": getattr(job, "language", None),
                    "has_transcript": bool(job.transcript_path)
                }
                results.append(job_data)

            return {
                "total": total_count,
                "offset": offset,
                "limit": limit,
                "results": results
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting transcripts for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def search_transcripts(
        self,
        user_id: str,
        query: str,
        db: Session,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search through user's transcripts."""
        try:
            # Get completed jobs with transcripts
            jobs = db.query(Job).filter(
                and_(
                    Job.user_id == user_id,
                    Job.status == JobStatusEnum.COMPLETED,
                    Job.transcript_path.isnot(None)
                )
            ).all()

            # Search through transcripts
            matches = []
            for job in jobs:
                transcript_path = Path(job.transcript_path)
                if not transcript_path.exists():
                    continue

                try:
                    async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        if query.lower() in content.lower():
                            matches.append({
                                "job_id": job.id,
                                "filename": job.original_filename,
                                "created_at": job.created_at.isoformat(),
                                "completed_at": job.finished_at.isoformat() if job.finished_at else None,
                                "model": job.model,
                                "excerpt": self._get_excerpt(content, query)
                            })
                except Exception as e:
                    logger.warning(f"Error reading transcript for job {job.id}: {e}")
                    continue

            # Apply pagination
            total_matches = len(matches)
            paginated_matches = matches[offset:offset + limit]

            return {
                "total": total_matches,
                "offset": offset,
                "limit": limit,
                "results": paginated_matches
            }

        except Exception as e:
            logger.error(f"Error searching transcripts for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def _get_excerpt(self, text: str, query: str, context_chars: int = 100) -> str:
        """Get excerpt of text around the search query."""
        query_pos = text.lower().find(query.lower())
        if query_pos == -1:
            return ""

        start = max(0, query_pos - context_chars)
        end = min(len(text), query_pos + len(query) + context_chars)
        
        excerpt = text[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."
            
        return excerpt

    async def export_transcript(
        self,
        job_id: str,
        user_id: str,
        export_format: str,
        db: Session
    ) -> Dict[str, Any]:
        """Export transcript in various formats (txt, json, srt)."""
        try:
            # Get transcript
            transcript_data = await self.get_transcript(job_id, user_id, db)
            
            if "transcript" not in transcript_data:
                raise HTTPException(
                    status_code=400,
                    detail="Transcript not available"
                )

            # Generate export filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            base_filename = f"transcript_{job_id}_{timestamp}"
            
            export_dir = storage.exports_dir / user_id
            export_dir.mkdir(parents=True, exist_ok=True)

            # Export based on format
            if export_format.lower() == "txt":
                export_path = export_dir / f"{base_filename}.txt"
                async with aiofiles.open(export_path, "w", encoding="utf-8") as f:
                    await f.write(transcript_data["transcript"])
                
            elif export_format.lower() == "json":
                export_path = export_dir / f"{base_filename}.json"
                export_data = {
                    "job_id": job_id,
                    "transcript": transcript_data["transcript"],
                    "metadata": {
                        "created_at": transcript_data["created_at"],
                        "completed_at": transcript_data["completed_at"],
                        "model": transcript_data["model"],
                        "language": transcript_data["language"],
                        "original_filename": transcript_data["original_filename"]
                    }
                }
                async with aiofiles.open(export_path, "w", encoding="utf-8") as f:
                    await f.write(json.dumps(export_data, indent=2))
                
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported export format: {export_format}"
                )

            return {
                "job_id": job_id,
                "export_format": export_format,
                "export_path": str(export_path),
                "message": "Export completed successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error exporting transcript for job {job_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_metrics(self) -> Dict[str, Any]:
        """Get transcript service metrics."""
        try:
            # Count transcript files
            transcript_count = sum(1 for _ in self.transcript_dir.glob("**/*.txt"))
            
            # Calculate total size
            total_size = sum(f.stat().st_size for f in self.transcript_dir.glob("**/*.txt"))

            return {
                "total_transcripts": transcript_count,
                "total_size_bytes": total_size,
                "export_formats": ["txt", "json"]
            }

        except Exception as e:
            logger.error(f"Error getting transcript metrics: {e}")
            return {
                "error": str(e)
            }


# Global service instance
transcript_service = ConsolidatedTranscriptService()
