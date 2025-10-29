"""
Comprehensive Test Suite for T025 Phase 5: Chunked Upload System

Tests chunked upload functionality, progress tracking, error recovery,
parallel processing, and performance validation.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json
import hashlib

from api.services.chunked_upload_service import (
    ChunkedUploadService, 
    UploadSession, 
    UploadStatus,
    ChunkProcessor,
    UploadProgressTracker
)
from api.routes.chunked_uploads import router as upload_router
from api.routes.upload_websockets import upload_websocket_notifier
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestChunkedUploadService:
    """Test the core chunked upload service."""
    
    @pytest.fixture
    def temp_upload_dir(self):
        """Create temporary upload directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def upload_service(self, temp_upload_dir):
        """Create upload service with temporary directory."""
        service = ChunkedUploadService()
        service.uploads_dir = temp_upload_dir
        service.sessions_dir = temp_upload_dir / "sessions"
        service.sessions_dir.mkdir(parents=True, exist_ok=True)
        return service
    
    @pytest.fixture
    def mock_websocket_service(self):
        """Mock WebSocket service."""
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_initialize_upload_success(self, upload_service):
        """Test successful upload initialization."""
        result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="test_file.mp3",
            file_size=5000000,  # 5MB
            model_name="small"
        )
        
        assert "session_id" in result
        assert result["chunk_size"] == upload_service.chunk_size
        assert result["total_chunks"] == 5  # 5MB / 1MB chunks
        assert "expires_at" in result
        
        # Verify session was saved
        session = await upload_service._load_session(result["session_id"])
        assert session is not None
        assert session.user_id == "test_user"
        assert session.original_filename == "test_file.mp3"
        assert session.status == UploadStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_initialize_upload_file_too_large(self, upload_service):
        """Test initialization with file too large."""
        with pytest.raises(Exception) as exc_info:
            await upload_service.initialize_upload(
                user_id="test_user",
                filename="huge_file.mp3",
                file_size=upload_service.max_file_size + 1
            )
        assert "too large" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_chunk_success(self, upload_service):
        """Test successful chunk upload."""
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="test_file.mp3",
            file_size=1024 * 1024 * 2  # 2MB
        )
        session_id = init_result["session_id"]
        
        # Create test chunk data
        chunk_data = b"A" * 1024 * 1024  # 1MB chunk
        
        # Upload chunk
        result = await upload_service.upload_chunk(
            session_id=session_id,
            chunk_number=0,
            chunk_data=chunk_data,
            user_id="test_user"
        )
        
        assert result["chunk_number"] == 0
        assert result["status"] == "uploaded"
        assert "chunk_hash" in result
        assert result["uploaded_chunks"] == 1
        assert result["total_chunks"] == 2
        assert result["progress_percent"] == 50.0
        
        # Verify chunk file was created
        session_dir = upload_service._get_session_dir(session_id)
        chunk_file = session_dir / "chunks" / "chunk_000000.tmp"
        assert chunk_file.exists()
        assert chunk_file.stat().st_size == len(chunk_data)
    
    @pytest.mark.asyncio
    async def test_upload_chunk_invalid_session(self, upload_service):
        """Test chunk upload with invalid session."""
        chunk_data = b"test data"
        
        with pytest.raises(Exception) as exc_info:
            await upload_service.upload_chunk(
                session_id="invalid_session",
                chunk_number=0,
                chunk_data=chunk_data,
                user_id="test_user"
            )
        assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_chunk_wrong_user(self, upload_service):
        """Test chunk upload with wrong user."""
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="test_file.mp3",
            file_size=1024 * 1024
        )
        session_id = init_result["session_id"]
        
        chunk_data = b"test data"
        
        with pytest.raises(Exception) as exc_info:
            await upload_service.upload_chunk(
                session_id=session_id,
                chunk_number=0,
                chunk_data=chunk_data,
                user_id="wrong_user"
            )
        assert "Access denied" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_finalize_upload_success(self, upload_service):
        """Test successful upload finalization."""
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="test_file.mp3",
            file_size=1024 * 1024  # 1MB (1 chunk)
        )
        session_id = init_result["session_id"]
        
        # Upload the single chunk
        chunk_data = b"A" * 1024 * 1024
        await upload_service.upload_chunk(
            session_id=session_id,
            chunk_number=0,
            chunk_data=chunk_data,
            user_id="test_user"
        )
        
        # Finalize upload
        result = await upload_service.finalize_upload(
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result["status"] == "completed"
        assert "job_id" in result
        assert "file_hash" in result
        assert "final_filename" in result
        
        # Verify final file was created
        final_file = upload_service.uploads_dir / result["final_filename"]
        assert final_file.exists()
        assert final_file.stat().st_size == len(chunk_data)
    
    @pytest.mark.asyncio
    async def test_finalize_upload_incomplete(self, upload_service):
        """Test finalization with missing chunks."""
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="test_file.mp3",
            file_size=1024 * 1024 * 2  # 2MB (2 chunks)
        )
        session_id = init_result["session_id"]
        
        # Upload only first chunk
        chunk_data = b"A" * 1024 * 1024
        await upload_service.upload_chunk(
            session_id=session_id,
            chunk_number=0,
            chunk_data=chunk_data,
            user_id="test_user"
        )
        
        # Try to finalize
        result = await upload_service.finalize_upload(
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result["status"] == "incomplete"
        assert result["missing_chunks"] == [1]
        assert result["uploaded_chunks"] == 1
        assert result["total_chunks"] == 2
    
    @pytest.mark.asyncio
    async def test_get_upload_status(self, upload_service):
        """Test getting upload status."""
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="test_file.mp3",
            file_size=1024 * 1024 * 3  # 3MB (3 chunks)
        )
        session_id = init_result["session_id"]
        
        # Upload first chunk
        chunk_data = b"A" * 1024 * 1024
        await upload_service.upload_chunk(
            session_id=session_id,
            chunk_number=0,
            chunk_data=chunk_data,
            user_id="test_user"
        )
        
        # Get status
        status = await upload_service.get_upload_status(
            session_id=session_id,
            user_id="test_user"
        )
        
        assert status["session_id"] == session_id
        assert status["status"] == "active"
        assert status["uploaded_chunks"] == 1
        assert status["total_chunks"] == 3
        assert status["progress_percent"] == 33.33
        assert status["missing_chunks"] == [1, 2]
        assert status["original_filename"] == "test_file.mp3"
    
    @pytest.mark.asyncio
    async def test_cancel_upload(self, upload_service):
        """Test upload cancellation."""
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="test_file.mp3",
            file_size=1024 * 1024
        )
        session_id = init_result["session_id"]
        
        # Cancel upload
        result = await upload_service.cancel_upload(
            session_id=session_id,
            user_id="test_user"
        )
        
        assert result["status"] == "cancelled"
        
        # Verify session status updated
        session = await upload_service._load_session(session_id)
        assert session.status == UploadStatus.CANCELLED
    
    def test_get_metrics(self, upload_service):
        """Test getting service metrics."""
        metrics = upload_service.get_metrics()
        
        assert "total_sessions" in metrics
        assert "active_sessions" in metrics
        assert "chunk_size" in metrics
        assert "max_parallel_chunks" in metrics
        assert "max_file_size" in metrics
        assert isinstance(metrics["total_sessions"], int)
        assert isinstance(metrics["chunk_size"], int)


class TestChunkProcessor:
    """Test the chunk processing functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def chunk_processor(self):
        """Create chunk processor."""
        return ChunkProcessor(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_process_chunk_success(self, chunk_processor, temp_dir):
        """Test successful chunk processing."""
        chunk_data = b"test chunk data"
        
        success, result = await chunk_processor.process_chunk(
            session_id="test_session",
            chunk_number=0,
            chunk_data=chunk_data,
            session_dir=temp_dir
        )
        
        assert success is True
        assert isinstance(result, str)  # chunk hash
        
        # Verify files created
        chunk_file = temp_dir / "chunks" / "chunk_000000.tmp"
        meta_file = temp_dir / "chunks" / "chunk_000000.meta"
        
        assert chunk_file.exists()
        assert meta_file.exists()
        
        # Verify chunk content
        with open(chunk_file, "rb") as f:
            saved_data = f.read()
        assert saved_data == chunk_data
        
        # Verify metadata
        with open(meta_file, "r") as f:
            metadata = json.load(f)
        
        assert metadata["chunk_number"] == 0
        assert metadata["size"] == len(chunk_data)
        assert "hash" in metadata
        assert "timestamp" in metadata
    
    @pytest.mark.asyncio
    async def test_process_chunk_empty_data(self, chunk_processor, temp_dir):
        """Test processing empty chunk data."""
        success, result = await chunk_processor.process_chunk(
            session_id="test_session",
            chunk_number=0,
            chunk_data=b"",
            session_dir=temp_dir
        )
        
        assert success is False
        assert "Empty chunk data" in result
    
    @pytest.mark.asyncio
    async def test_assemble_file_success(self, chunk_processor, temp_dir):
        """Test successful file assembly."""
        # Create test session
        session = UploadSession(
            session_id="test_session",
            user_id="test_user",
            original_filename="test.mp3",
            total_chunks=3,
            chunk_size=1024,
            total_size=3072,
            file_hash=None,
            uploaded_chunks={0, 1, 2},
            status=UploadStatus.ACTIVE,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Create chunks
        chunks_dir = temp_dir / "chunks"
        chunks_dir.mkdir(parents=True)
        
        chunk_data = [b"chunk0", b"chunk1", b"chunk2"]
        for i, data in enumerate(chunk_data):
            chunk_file = chunks_dir / f"chunk_{i:06d}.tmp"
            with open(chunk_file, "wb") as f:
                f.write(data)
        
        # Assemble file
        output_path = temp_dir / "assembled_file.mp3"
        success, result = await chunk_processor.assemble_file(
            session=session,
            session_dir=temp_dir,
            output_path=output_path
        )
        
        assert success is True
        assert isinstance(result, str)  # file hash
        
        # Verify assembled file
        assert output_path.exists()
        with open(output_path, "rb") as f:
            assembled_data = f.read()
        
        expected_data = b"chunk0chunk1chunk2"
        assert assembled_data == expected_data
        
        # Verify hash
        expected_hash = hashlib.sha256(expected_data).hexdigest()
        assert result == expected_hash
    
    @pytest.mark.asyncio
    async def test_assemble_file_missing_chunks(self, chunk_processor, temp_dir):
        """Test file assembly with missing chunks."""
        session = UploadSession(
            session_id="test_session",
            user_id="test_user",
            original_filename="test.mp3",
            total_chunks=3,
            chunk_size=1024,
            total_size=3072,
            file_hash=None,
            uploaded_chunks={0, 2},  # Missing chunk 1
            status=UploadStatus.ACTIVE,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Create only some chunks
        chunks_dir = temp_dir / "chunks"
        chunks_dir.mkdir(parents=True)
        
        chunk_file_0 = chunks_dir / "chunk_000000.tmp"
        chunk_file_2 = chunks_dir / "chunk_000002.tmp"
        
        with open(chunk_file_0, "wb") as f:
            f.write(b"chunk0")
        with open(chunk_file_2, "wb") as f:
            f.write(b"chunk2")
        
        # Try to assemble
        output_path = temp_dir / "assembled_file.mp3"
        success, result = await chunk_processor.assemble_file(
            session=session,
            session_dir=temp_dir,
            output_path=output_path
        )
        
        assert success is False
        assert "Missing chunks: [1]" in result
    
    def test_cleanup(self, chunk_processor):
        """Test processor cleanup."""
        chunk_processor.cleanup()
        # Should not raise any exceptions


class TestUploadProgressTracker:
    """Test upload progress tracking."""
    
    @pytest.fixture
    def mock_websocket_service(self):
        """Mock WebSocket service."""
        return AsyncMock()
    
    @pytest.fixture
    def progress_tracker(self, mock_websocket_service):
        """Create progress tracker with mock WebSocket."""
        return UploadProgressTracker(mock_websocket_service)
    
    @pytest.mark.asyncio
    async def test_update_progress(self, progress_tracker, mock_websocket_service):
        """Test progress update."""
        await progress_tracker.update_progress(
            session_id="test_session",
            user_id="test_user",
            event_type="test_event",
            data={"test": "data"}
        )
        
        # Verify WebSocket called
        mock_websocket_service.send_to_user.assert_called_once()
        call_args = mock_websocket_service.send_to_user.call_args
        
        assert call_args[0][0] == "test_user"
        assert call_args[0][1] == "upload_progress"
        
        message = call_args[0][2]
        assert message["session_id"] == "test_session"
        assert message["event_type"] == "test_event"
        assert message["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_notify_chunk_uploaded(self, progress_tracker, mock_websocket_service):
        """Test chunk upload notification."""
        await progress_tracker.notify_chunk_uploaded(
            session_id="test_session",
            user_id="test_user",
            chunk_number=1,
            total_chunks=5,
            bytes_uploaded=2048,
            total_bytes=5120
        )
        
        # Verify WebSocket called with correct data
        mock_websocket_service.send_to_user.assert_called_once()
        call_args = mock_websocket_service.send_to_user.call_args
        message = call_args[0][2]
        
        assert message["event_type"] == "chunk_uploaded"
        assert message["chunk_number"] == 1
        assert message["total_chunks"] == 5
        assert message["progress_percent"] == 40.0  # 2/5 chunks
    
    @pytest.mark.asyncio
    async def test_notify_assembly_started(self, progress_tracker, mock_websocket_service):
        """Test assembly start notification."""
        await progress_tracker.notify_assembly_started(
            session_id="test_session",
            user_id="test_user"
        )
        
        mock_websocket_service.send_to_user.assert_called_once()
        call_args = mock_websocket_service.send_to_user.call_args
        message = call_args[0][2]
        
        assert message["event_type"] == "assembly_started"
        assert "Assembling" in message["message"]
    
    @pytest.mark.asyncio
    async def test_notify_upload_completed(self, progress_tracker, mock_websocket_service):
        """Test upload completion notification."""
        await progress_tracker.notify_upload_completed(
            session_id="test_session",
            user_id="test_user",
            job_id="job_123"
        )
        
        mock_websocket_service.send_to_user.assert_called_once()
        call_args = mock_websocket_service.send_to_user.call_args
        message = call_args[0][2]
        
        assert message["event_type"] == "upload_completed"
        assert message["job_id"] == "job_123"
    
    @pytest.mark.asyncio
    async def test_notify_upload_failed(self, progress_tracker, mock_websocket_service):
        """Test upload failure notification."""
        await progress_tracker.notify_upload_failed(
            session_id="test_session",
            user_id="test_user",
            error="Test error"
        )
        
        mock_websocket_service.send_to_user.assert_called_once()
        call_args = mock_websocket_service.send_to_user.call_args
        message = call_args[0][2]
        
        assert message["event_type"] == "upload_failed"
        assert message["error"] == "Test error"


class TestUploadAPIEndpoints:
    """Test the upload API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create FastAPI app with upload routes."""
        app = FastAPI()
        app.include_router(upload_router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_upload_service(self):
        """Mock upload service."""
        return AsyncMock()
    
    def test_initialize_upload_endpoint(self, client, mock_upload_service):
        """Test initialize upload endpoint."""
        with patch('api.routes.chunked_uploads.chunked_upload_service', mock_upload_service):
            mock_upload_service.initialize_upload.return_value = {
                "session_id": "test_session",
                "chunk_size": 1024,
                "total_chunks": 5,
                "expires_at": "2024-01-01T00:00:00"
            }
            
            response = client.post("/uploads/initialize", json={
                "filename": "test.mp3",
                "file_size": 5120,
                "model_name": "small"
            }, headers={"X-User-ID": "test_user"})
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test_session"
            assert data["chunk_size"] == 1024
            assert data["total_chunks"] == 5
    
    def test_upload_chunk_endpoint(self, client, mock_upload_service):
        """Test upload chunk endpoint."""
        with patch('api.routes.chunked_uploads.chunked_upload_service', mock_upload_service):
            mock_upload_service.upload_chunk.return_value = {
                "chunk_number": 0,
                "status": "uploaded",
                "chunk_hash": "abc123",
                "uploaded_chunks": 1,
                "total_chunks": 5,
                "progress_percent": 20.0
            }
            
            # Create test file data
            test_data = b"test chunk data"
            
            response = client.post(
                "/uploads/test_session/chunks/0",
                files={"chunk_data": ("chunk", test_data, "application/octet-stream")},
                headers={"X-User-ID": "test_user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["chunk_number"] == 0
            assert data["status"] == "uploaded"
            assert data["progress_percent"] == 20.0
    
    def test_get_upload_status_endpoint(self, client, mock_upload_service):
        """Test get upload status endpoint."""
        with patch('api.routes.chunked_uploads.chunked_upload_service', mock_upload_service):
            mock_upload_service.get_upload_status.return_value = {
                "session_id": "test_session",
                "status": "active",
                "uploaded_chunks": 2,
                "total_chunks": 5,
                "progress_percent": 40.0,
                "missing_chunks": [2, 3, 4],
                "expires_at": "2024-01-01T00:00:00",
                "original_filename": "test.mp3"
            }
            
            response = client.get(
                "/uploads/test_session/status",
                headers={"X-User-ID": "test_user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test_session"
            assert data["status"] == "active"
            assert data["progress_percent"] == 40.0
    
    def test_finalize_upload_endpoint(self, client, mock_upload_service):
        """Test finalize upload endpoint."""
        with patch('api.routes.chunked_uploads.chunked_upload_service', mock_upload_service):
            mock_upload_service.finalize_upload.return_value = {
                "status": "completed",
                "job_id": "job_123",
                "file_hash": "def456",
                "final_filename": "session_test.mp3"
            }
            
            response = client.post(
                "/uploads/test_session/finalize",
                headers={"X-User-ID": "test_user"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["job_id"] == "job_123"
            assert data["file_hash"] == "def456"


class TestPerformanceScenarios:
    """Test performance and stress scenarios."""
    
    @pytest.fixture
    def upload_service(self):
        """Create upload service for performance testing."""
        temp_dir = tempfile.mkdtemp()
        service = ChunkedUploadService()
        service.uploads_dir = Path(temp_dir)
        service.sessions_dir = Path(temp_dir) / "sessions"
        service.sessions_dir.mkdir(parents=True, exist_ok=True)
        yield service
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, upload_service):
        """Test multiple concurrent upload sessions."""
        num_concurrent = 5
        file_size = 1024 * 1024 * 2  # 2MB each
        
        # Initialize concurrent uploads
        init_tasks = []
        for i in range(num_concurrent):
            task = upload_service.initialize_upload(
                user_id=f"user_{i}",
                filename=f"file_{i}.mp3",
                file_size=file_size
            )
            init_tasks.append(task)
        
        init_results = await asyncio.gather(*init_tasks)
        
        # Verify all initialized successfully
        assert len(init_results) == num_concurrent
        for result in init_results:
            assert "session_id" in result
            assert result["total_chunks"] == 2
        
        # Upload first chunk for each session concurrently
        chunk_data = b"A" * 1024 * 1024  # 1MB
        upload_tasks = []
        
        for i, result in enumerate(init_results):
            task = upload_service.upload_chunk(
                session_id=result["session_id"],
                chunk_number=0,
                chunk_data=chunk_data,
                user_id=f"user_{i}"
            )
            upload_tasks.append(task)
        
        upload_results = await asyncio.gather(*upload_tasks)
        
        # Verify all uploads successful
        assert len(upload_results) == num_concurrent
        for result in upload_results:
            assert result["status"] == "uploaded"
            assert result["progress_percent"] == 50.0
    
    @pytest.mark.asyncio
    async def test_large_file_upload(self, upload_service):
        """Test uploading a large file (simulated)."""
        file_size = 1024 * 1024 * 100  # 100MB
        
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="large_file.mp3",
            file_size=file_size
        )
        
        session_id = init_result["session_id"]
        total_chunks = init_result["total_chunks"]
        
        assert total_chunks == 100  # 100 chunks of 1MB each
        
        # Upload chunks in batches to simulate real-world scenario
        chunk_data = b"A" * 1024 * 1024  # 1MB chunk
        batch_size = 4  # Upload 4 chunks at a time
        
        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            
            # Upload batch concurrently
            batch_tasks = []
            for chunk_num in range(batch_start, batch_end):
                task = upload_service.upload_chunk(
                    session_id=session_id,
                    chunk_number=chunk_num,
                    chunk_data=chunk_data,
                    user_id="test_user"
                )
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Verify batch uploaded successfully
            for result in batch_results:
                assert result["status"] == "uploaded"
        
        # Verify all chunks uploaded
        status = await upload_service.get_upload_status(session_id, "test_user")
        assert status["uploaded_chunks"] == total_chunks
        assert status["progress_percent"] == 100.0
        assert len(status["missing_chunks"]) == 0
    
    @pytest.mark.asyncio
    async def test_resume_functionality(self, upload_service):
        """Test upload resume after interruption."""
        # Initialize upload
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="resume_test.mp3",
            file_size=1024 * 1024 * 5  # 5MB (5 chunks)
        )
        
        session_id = init_result["session_id"]
        chunk_data = b"A" * 1024 * 1024
        
        # Upload first 3 chunks
        for i in range(3):
            await upload_service.upload_chunk(
                session_id=session_id,
                chunk_number=i,
                chunk_data=chunk_data,
                user_id="test_user"
            )
        
        # Check status (simulating interruption check)
        status = await upload_service.get_upload_status(session_id, "test_user")
        assert status["uploaded_chunks"] == 3
        assert status["missing_chunks"] == [3, 4]
        assert status["progress_percent"] == 60.0
        
        # Resume by uploading missing chunks
        for chunk_num in status["missing_chunks"]:
            result = await upload_service.upload_chunk(
                session_id=session_id,
                chunk_number=chunk_num,
                chunk_data=chunk_data,
                user_id="test_user"
            )
            assert result["status"] == "uploaded"
        
        # Verify complete
        final_status = await upload_service.get_upload_status(session_id, "test_user")
        assert final_status["uploaded_chunks"] == 5
        assert final_status["progress_percent"] == 100.0
        assert len(final_status["missing_chunks"]) == 0
    
    @pytest.mark.asyncio
    async def test_session_expiration(self, upload_service):
        """Test session expiration handling."""
        # Create session with short expiration for testing
        init_result = await upload_service.initialize_upload(
            user_id="test_user",
            filename="expire_test.mp3",
            file_size=1024 * 1024
        )
        
        session_id = init_result["session_id"]
        
        # Manually expire the session
        session = await upload_service._load_session(session_id)
        session.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        await upload_service._save_session(session)
        
        # Try to upload chunk to expired session
        chunk_data = b"test data"
        
        with pytest.raises(Exception) as exc_info:
            await upload_service.upload_chunk(
                session_id=session_id,
                chunk_number=0,
                chunk_data=chunk_data,
                user_id="test_user"
            )
        assert "expired" in str(exc_info.value)
        
        # Verify session marked as expired
        updated_session = await upload_service._load_session(session_id)
        assert updated_session.status == UploadStatus.EXPIRED


if __name__ == "__main__":
    # Run specific test groups
    import sys
    
    if len(sys.argv) > 1:
        test_group = sys.argv[1]
        if test_group == "service":
            pytest.main(["-v", "TestChunkedUploadService"])
        elif test_group == "processor":
            pytest.main(["-v", "TestChunkProcessor"])
        elif test_group == "tracker":
            pytest.main(["-v", "TestUploadProgressTracker"])
        elif test_group == "api":
            pytest.main(["-v", "TestUploadAPIEndpoints"])
        elif test_group == "performance":
            pytest.main(["-v", "TestPerformanceScenarios"])
        else:
            print("Available test groups: service, processor, tracker, api, performance")
    else:
        # Run all tests
        pytest.main(["-v", __file__])
