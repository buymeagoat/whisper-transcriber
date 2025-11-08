"""
Consolidated Upload Service

This service provides a unified interface for handling both direct and chunked uploads,
managing file validation, storage, and job creation.
"""

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, BinaryIO

import aiofiles
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from api.models import Job, JobStatusEnum
from api.settings import settings
from api.services.chunked_upload_service import ChunkedUploadService
from api.utils.logger import get_system_logger
from api.paths import storage

logger = get_system_logger("upload_service")

# Maximum size for direct uploads (100MB)
MAX_DIRECT_UPLOAD_SIZE = 100 * 1024 * 1024

# Supported audio formats
SUPPORTED_FORMATS = {
    'audio/wav': '.wav',
    'audio/x-wav': '.wav',
    'audio/mp3': '.mp3',
    'audio/mpeg': '.mp3',
    'audio/ogg': '.ogg',
    'audio/x-m4a': '.m4a',
    'audio/aac': '.aac',
    'audio/flac': '.flac',
}

class ConsolidatedUploadService:
    """Unified service for handling file uploads."""

    def __init__(self):
        """Initialize the upload service."""
        self.chunked_service = ChunkedUploadService()
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def handle_direct_upload(
        self,
        file: UploadFile,
        user_id: str,
        db: Session,
        model_name: str = "small",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle direct file upload for smaller files."""
        try:
            # Validate file format
            if file.content_type not in SUPPORTED_FORMATS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format. Supported types: {', '.join(SUPPORTED_FORMATS.keys())}"
                )

            # Read file content
            content = await file.read()
            if len(content) > MAX_DIRECT_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large for direct upload. Maximum size: {MAX_DIRECT_UPLOAD_SIZE} bytes. Use chunked upload instead."
                )

            # Generate unique filename
            file_id = str(uuid.uuid4())
            extension = SUPPORTED_FORMATS[file.content_type]
            saved_filename = f"{file_id}{extension}"
            file_path = self.upload_dir / saved_filename

            # Save file
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            # Create job
            job = Job(
                id=file_id,
                original_filename=file.filename,
                saved_filename=str(file_path),
                model=model_name,
                status=JobStatusEnum.QUEUED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(job)
            db.commit()

            from api.services.job_queue import job_queue

            job_queue.submit_job(
                "transcribe_audio",
                job_id=job.id,
                file_path=str(file_path),
            )

            logger.info(f"Direct upload completed for user {user_id}, job {job.id}")

            return {
                "job_id": job.id,
                "status": job.status.value,
                "message": "File uploaded successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling direct upload: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def initialize_chunked_upload(
        self,
        filename: str,
        file_size: int,
        user_id: str,
        file_hash: Optional[str] = None,
        model_name: str = "small",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize a chunked upload session."""
        # Validate file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in SUPPORTED_FORMATS.values():
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported extensions: {', '.join(SUPPORTED_FORMATS.values())}"
            )

        return await self.chunked_service.initialize_upload(
            user_id=user_id,
            filename=filename,
            file_size=file_size,
            file_hash=file_hash,
            model_name=model_name,
            language=language
        )

    async def handle_chunk_upload(
        self,
        session_id: str,
        chunk_number: int,
        chunk_data: bytes,
        user_id: str
    ) -> Dict[str, Any]:
        """Handle upload of a single chunk."""
        return await self.chunked_service.upload_chunk(
            session_id=session_id,
            chunk_number=chunk_number,
            chunk_data=chunk_data,
            user_id=user_id
        )

    async def finalize_chunked_upload(
        self,
        session_id: str,
        user_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Finalize a chunked upload and create the job."""
        from api.services.job_queue import job_queue
        
        result = await self.chunked_service.finalize_upload(session_id, user_id)

        if result["status"] == "completed":
            # Job is already created by chunked_service._create_transcription_job
            # We just need to verify it was queued successfully
            logger.info(f"Chunked upload finalized, job {result['job_id']} has been queued")

        return result

    async def get_upload_status(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get status of a chunked upload."""
        return await self.chunked_service.get_upload_status(session_id, user_id)

    async def cancel_upload(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Cancel an in-progress chunked upload."""
        return await self.chunked_service.cancel_upload(session_id, user_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Get upload service metrics."""
        return self.chunked_service.get_metrics()


# Global service instance
upload_service = ConsolidatedUploadService()
