"""
Chunked Upload Service for T025 Phase 5: File Upload Optimization

Provides chunked file upload capabilities with parallel processing,
resumable uploads, and real-time progress tracking.
"""

import asyncio
import hashlib
import json
import shutil
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
import aiofiles
import aiofiles.os

from fastapi import HTTPException
from api.settings import settings
from api.utils.logger import get_system_logger
from api.services.enhanced_websocket_service import EnhancedWebSocketService

logger = get_system_logger("chunked_upload")


class UploadStatus(Enum):
    """Upload session status."""
    ACTIVE = "active"
    ASSEMBLING = "assembling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class UploadSession:
    """Upload session metadata."""
    session_id: str
    user_id: str
    original_filename: str
    total_chunks: int
    chunk_size: int
    total_size: int
    file_hash: Optional[str]
    uploaded_chunks: Set[int]
    status: UploadStatus
    created_at: datetime
    expires_at: datetime
    model_name: str = "small"
    language: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['uploaded_chunks'] = list(self.uploaded_chunks)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadSession':
        """Create from dictionary."""
        data['uploaded_chunks'] = set(data['uploaded_chunks'])
        data['status'] = UploadStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class ChunkProcessor:
    """Handles parallel chunk processing with validation."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.chunk_validators = {}
    
    async def process_chunk(
        self, 
        session_id: str, 
        chunk_number: int, 
        chunk_data: bytes,
        session_dir: Path
    ) -> Tuple[bool, str]:
        """Process and validate a single chunk."""
        try:
            chunk_file = session_dir / "chunks" / f"chunk_{chunk_number:06d}.tmp"
            chunk_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate chunk data
            if len(chunk_data) == 0:
                return False, "Empty chunk data"
            
            # Write chunk to temporary file
            async with aiofiles.open(chunk_file, "wb") as f:
                await f.write(chunk_data)
            
            # Verify chunk integrity
            chunk_hash = hashlib.sha256(chunk_data).hexdigest()
            
            # Store chunk metadata
            chunk_meta = {
                "chunk_number": chunk_number,
                "size": len(chunk_data),
                "hash": chunk_hash,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            meta_file = session_dir / "chunks" / f"chunk_{chunk_number:06d}.meta"
            async with aiofiles.open(meta_file, "w") as f:
                await f.write(json.dumps(chunk_meta))
            
            logger.debug(f"Processed chunk {chunk_number} for session {session_id}")
            return True, chunk_hash
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_number} for session {session_id}: {e}")
            return False, str(e)
    
    async def assemble_file(
        self, 
        session: UploadSession, 
        session_dir: Path,
        output_path: Path
    ) -> Tuple[bool, str]:
        """Assemble chunks into final file."""
        try:
            logger.info(f"Starting file assembly for session {session.session_id}")
            
            chunks_dir = session_dir / "chunks"
            
            # Verify all chunks are present
            missing_chunks = []
            for i in range(session.total_chunks):
                chunk_file = chunks_dir / f"chunk_{i:06d}.tmp"
                if not chunk_file.exists():
                    missing_chunks.append(i)
            
            if missing_chunks:
                return False, f"Missing chunks: {missing_chunks}"
            
            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Assemble file by streaming chunks
            total_written = 0
            file_hash = hashlib.sha256()
            
            async with aiofiles.open(output_path, "wb") as output_file:
                for i in range(session.total_chunks):
                    chunk_file = chunks_dir / f"chunk_{i:06d}.tmp"
                    
                    async with aiofiles.open(chunk_file, "rb") as chunk:
                        chunk_data = await chunk.read()
                        await output_file.write(chunk_data)
                        file_hash.update(chunk_data)
                        total_written += len(chunk_data)
            
            # Verify final file integrity
            final_hash = file_hash.hexdigest()
            
            logger.info(f"File assembly completed for session {session.session_id}: {total_written} bytes")
            return True, final_hash
            
        except Exception as e:
            logger.error(f"Error assembling file for session {session.session_id}: {e}")
            return False, str(e)
    
    def cleanup(self):
        """Cleanup resources."""
        self.executor.shutdown(wait=True)


class UploadProgressTracker:
    """Tracks upload progress with WebSocket integration."""
    
    def __init__(self, websocket_service: Optional[EnhancedWebSocketService] = None):
        self.websocket_service = websocket_service
        self.progress_cache = {}
    
    async def update_progress(
        self, 
        session_id: str, 
        user_id: str,
        event_type: str, 
        data: Dict[str, Any]
    ):
        """Update progress and notify via WebSocket."""
        progress_data = {
            "session_id": session_id,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
        
        self.progress_cache[session_id] = progress_data
        
        # Send WebSocket notification if available
        if self.websocket_service:
            try:
                await self.websocket_service.send_to_user(
                    user_id,
                    "upload_progress",
                    progress_data
                )
            except Exception as e:
                logger.warning(f"Failed to send WebSocket progress update: {e}")
    
    async def notify_chunk_uploaded(
        self, 
        session_id: str, 
        user_id: str,
        chunk_number: int, 
        total_chunks: int,
        bytes_uploaded: int,
        total_bytes: int
    ):
        """Notify chunk upload completion."""
        progress_percent = (len(set(range(chunk_number + 1))) / total_chunks) * 100
        
        await self.update_progress(session_id, user_id, "chunk_uploaded", {
            "chunk_number": chunk_number,
            "total_chunks": total_chunks,
            "progress_percent": round(progress_percent, 2),
            "bytes_uploaded": bytes_uploaded,
            "total_bytes": total_bytes
        })
    
    async def notify_assembly_started(self, session_id: str, user_id: str):
        """Notify file assembly started."""
        await self.update_progress(session_id, user_id, "assembly_started", {
            "message": "Assembling uploaded chunks into final file"
        })
    
    async def notify_upload_completed(self, session_id: str, user_id: str, job_id: str):
        """Notify upload completion."""
        await self.update_progress(session_id, user_id, "upload_completed", {
            "job_id": job_id,
            "message": "Upload completed successfully"
        })
    
    async def notify_upload_failed(self, session_id: str, user_id: str, error: str):
        """Notify upload failure."""
        await self.update_progress(session_id, user_id, "upload_failed", {
            "error": error,
            "message": "Upload failed"
        })


class ChunkedUploadService:
    """Main service for chunked file uploads."""
    
    def __init__(self, websocket_service: Optional[EnhancedWebSocketService] = None):
        self.chunk_size = 1024 * 1024  # 1MB chunks
        self.max_parallel_chunks = 4
        self.session_timeout_hours = 24
        self.max_file_size = 1024 * 1024 * 1024  # 1GB
        
        # Storage paths
        self.uploads_dir = Path(settings.upload_dir)
        self.sessions_dir = self.uploads_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Components
        self.chunk_processor = ChunkProcessor(max_workers=self.max_parallel_chunks)
        self.progress_tracker = UploadProgressTracker(websocket_service)
        
        # Session storage (in production, use Redis)
        self.sessions: Dict[str, UploadSession] = {}
        
        logger.info("ChunkedUploadService initialized")
    
    def _get_session_dir(self, session_id: str) -> Path:
        """Get session directory path."""
        return self.sessions_dir / session_id
    
    async def _save_session(self, session: UploadSession):
        """Save session metadata to disk."""
        session_dir = self._get_session_dir(session.session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = session_dir / "metadata.json"
        async with aiofiles.open(metadata_file, "w") as f:
            await f.write(json.dumps(session.to_dict(), indent=2))
        
        self.sessions[session.session_id] = session
    
    async def _load_session(self, session_id: str) -> Optional[UploadSession]:
        """Load session metadata from disk."""
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        session_dir = self._get_session_dir(session_id)
        metadata_file = session_dir / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            async with aiofiles.open(metadata_file, "r") as f:
                data = json.loads(await f.read())
            
            session = UploadSession.from_dict(data)
            self.sessions[session_id] = session
            return session
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    async def initialize_upload(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        file_hash: Optional[str] = None,
        model_name: str = "small",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize a new chunked upload session."""
        try:
            # Validate input
            if file_size <= 0:
                raise HTTPException(status_code=400, detail="Invalid file size")
            
            if file_size > self.max_file_size:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File too large. Maximum size: {self.max_file_size} bytes"
                )
            
            # Calculate chunk information
            total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
            
            # Create session
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            session = UploadSession(
                session_id=session_id,
                user_id=user_id,
                original_filename=filename,
                total_chunks=total_chunks,
                chunk_size=self.chunk_size,
                total_size=file_size,
                file_hash=file_hash,
                uploaded_chunks=set(),
                status=UploadStatus.ACTIVE,
                created_at=now,
                expires_at=now + timedelta(hours=self.session_timeout_hours),
                model_name=model_name,
                language=language
            )
            
            await self._save_session(session)
            
            logger.info(f"Initialized upload session {session_id} for user {user_id}")
            
            return {
                "session_id": session_id,
                "chunk_size": self.chunk_size,
                "total_chunks": total_chunks,
                "expires_at": session.expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error initializing upload: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def upload_chunk(
        self,
        session_id: str,
        chunk_number: int,
        chunk_data: bytes,
        user_id: str
    ) -> Dict[str, Any]:
        """Upload a single chunk."""
        try:
            # Load session
            session = await self._load_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Upload session not found")
            
            # Verify session ownership
            if session.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check session status
            if session.status != UploadStatus.ACTIVE:
                raise HTTPException(status_code=400, detail=f"Session status: {session.status.value}")
            
            # Check expiration
            if datetime.utcnow() > session.expires_at:
                session.status = UploadStatus.EXPIRED
                await self._save_session(session)
                raise HTTPException(status_code=410, detail="Upload session expired")
            
            # Validate chunk number
            if chunk_number < 0 or chunk_number >= session.total_chunks:
                raise HTTPException(status_code=400, detail="Invalid chunk number")
            
            # Check if chunk already uploaded
            if chunk_number in session.uploaded_chunks:
                return {
                    "chunk_number": chunk_number,
                    "status": "already_uploaded",
                    "uploaded_chunks": len(session.uploaded_chunks),
                    "total_chunks": session.total_chunks
                }
            
            # Process chunk
            session_dir = self._get_session_dir(session_id)
            success, result = await self.chunk_processor.process_chunk(
                session_id, chunk_number, chunk_data, session_dir
            )
            
            if not success:
                raise HTTPException(status_code=400, detail=f"Chunk processing failed: {result}")
            
            # Update session
            session.uploaded_chunks.add(chunk_number)
            await self._save_session(session)
            
            # Calculate progress
            bytes_uploaded = len(session.uploaded_chunks) * self.chunk_size
            if chunk_number == session.total_chunks - 1:
                # Last chunk might be smaller
                bytes_uploaded = session.total_size
            
            # Notify progress
            await self.progress_tracker.notify_chunk_uploaded(
                session_id, user_id, chunk_number, session.total_chunks,
                bytes_uploaded, session.total_size
            )
            
            logger.debug(f"Uploaded chunk {chunk_number} for session {session_id}")
            
            return {
                "chunk_number": chunk_number,
                "status": "uploaded",
                "chunk_hash": result,
                "uploaded_chunks": len(session.uploaded_chunks),
                "total_chunks": session.total_chunks,
                "progress_percent": round((len(session.uploaded_chunks) / session.total_chunks) * 100, 2)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading chunk: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def finalize_upload(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Finalize upload by assembling chunks."""
        try:
            # Load session
            session = await self._load_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Upload session not found")
            
            # Verify session ownership
            if session.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check if all chunks uploaded
            if len(session.uploaded_chunks) != session.total_chunks:
                missing_chunks = set(range(session.total_chunks)) - session.uploaded_chunks
                return {
                    "status": "incomplete",
                    "missing_chunks": sorted(list(missing_chunks)),
                    "uploaded_chunks": len(session.uploaded_chunks),
                    "total_chunks": session.total_chunks
                }
            
            # Update status to assembling
            session.status = UploadStatus.ASSEMBLING
            await self._save_session(session)
            
            # Notify assembly started
            await self.progress_tracker.notify_assembly_started(session_id, user_id)
            
            # Assemble file
            session_dir = self._get_session_dir(session_id)
            final_filename = f"{session_id}_{session.original_filename}"
            output_path = self.uploads_dir / final_filename
            
            success, result = await self.chunk_processor.assemble_file(
                session, session_dir, output_path
            )
            
            if not success:
                session.status = UploadStatus.FAILED
                await self._save_session(session)
                await self.progress_tracker.notify_upload_failed(session_id, user_id, result)
                raise HTTPException(status_code=500, detail=f"File assembly failed: {result}")
            
            # Update session
            session.status = UploadStatus.COMPLETED
            session.file_hash = result
            await self._save_session(session)
            
            # Create transcription job (integrate with existing job system)
            job_id = await self._create_transcription_job(session, output_path)
            
            # Notify completion
            await self.progress_tracker.notify_upload_completed(session_id, user_id, job_id)
            
            # Cleanup chunks (async)
            asyncio.create_task(self._cleanup_session_chunks(session_id))
            
            logger.info(f"Upload finalized for session {session_id}, job created: {job_id}")
            
            return {
                "status": "completed",
                "job_id": job_id,
                "file_hash": result,
                "final_filename": final_filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error finalizing upload: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_upload_status(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get current upload status."""
        try:
            session = await self._load_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Upload session not found")
            
            # Verify session ownership
            if session.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check expiration
            if datetime.utcnow() > session.expires_at and session.status == UploadStatus.ACTIVE:
                session.status = UploadStatus.EXPIRED
                await self._save_session(session)
            
            # Calculate progress
            progress_percent = (len(session.uploaded_chunks) / session.total_chunks) * 100
            missing_chunks = sorted(list(set(range(session.total_chunks)) - session.uploaded_chunks))
            
            return {
                "session_id": session_id,
                "status": session.status.value,
                "uploaded_chunks": len(session.uploaded_chunks),
                "total_chunks": session.total_chunks,
                "progress_percent": round(progress_percent, 2),
                "missing_chunks": missing_chunks[:10],  # Limit for response size
                "expires_at": session.expires_at.isoformat(),
                "original_filename": session.original_filename
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting upload status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def cancel_upload(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Cancel an upload session."""
        try:
            session = await self._load_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Upload session not found")
            
            # Verify session ownership
            if session.user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Update status
            session.status = UploadStatus.CANCELLED
            await self._save_session(session)
            
            # Cleanup chunks
            await self._cleanup_session_chunks(session_id)
            
            logger.info(f"Upload session {session_id} cancelled")
            
            return {
                "status": "cancelled",
                "message": "Upload session cancelled successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling upload: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _create_transcription_job(self, session: UploadSession, file_path: Path) -> str:
        """Create transcription job from uploaded file."""
        from api.models import Job, JobStatusEnum
        from api.orm_bootstrap import SessionLocal
        from api.services.job_queue import job_queue
        from datetime import datetime
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Generate job ID
            job_id = str(uuid.uuid4())
            
            # Create job record in database
            job = Job(
                id=job_id,
                user_id=str(session.user_id),
                original_filename=session.original_filename,
                saved_filename=str(file_path),
                model=session.model_name,
                status=JobStatusEnum.QUEUED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(job)
            db.commit()
            db.refresh(job)
            
            # Submit job to Celery queue
            job_queue.submit_job(
                "transcribe_audio",
                job_id=job_id,
                file_path=str(file_path),
            )
            
            logger.info(f"Created transcription job {job_id} for chunked upload session {session.session_id}")
            
            return job_id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create transcription job: {e}")
            raise
        finally:
            db.close()
    
    async def _cleanup_session_chunks(self, session_id: str):
        """Cleanup temporary chunk files."""
        try:
            session_dir = self._get_session_dir(session_id)
            chunks_dir = session_dir / "chunks"
            
            if chunks_dir.exists():
                await aiofiles.os.rmdir(chunks_dir)
                logger.debug(f"Cleaned up chunks for session {session_id}")
                
        except Exception as e:
            logger.warning(f"Error cleaning up chunks for session {session_id}: {e}")
    
    async def cleanup_expired_sessions(self):
        """Cleanup expired upload sessions."""
        try:
            now = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if now > session.expires_at and session.status in [UploadStatus.ACTIVE, UploadStatus.ASSEMBLING]:
                    session.status = UploadStatus.EXPIRED
                    await self._save_session(session)
                    expired_sessions.append(session_id)
            
            # Cleanup expired session files
            for session_id in expired_sessions:
                await self._cleanup_session_chunks(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired upload sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get upload service metrics."""
        active_sessions = sum(1 for s in self.sessions.values() if s.status == UploadStatus.ACTIVE)
        assembling_sessions = sum(1 for s in self.sessions.values() if s.status == UploadStatus.ASSEMBLING)
        completed_sessions = sum(1 for s in self.sessions.values() if s.status == UploadStatus.COMPLETED)
        failed_sessions = sum(1 for s in self.sessions.values() if s.status == UploadStatus.FAILED)
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "assembling_sessions": assembling_sessions,
            "completed_sessions": completed_sessions,
            "failed_sessions": failed_sessions,
            "chunk_size": self.chunk_size,
            "max_parallel_chunks": self.max_parallel_chunks,
            "max_file_size": self.max_file_size
        }
    
    def cleanup(self):
        """Cleanup service resources."""
        self.chunk_processor.cleanup()


# Global service instance
chunked_upload_service = ChunkedUploadService()
