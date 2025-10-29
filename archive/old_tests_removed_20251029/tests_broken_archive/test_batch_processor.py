#!/usr/bin/env python3
"""
T027 Advanced Features: Batch Processing Tests
Tests for batch upload and processing functionality.
"""

import pytest
import uuid
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
from io import BytesIO

from api.services.batch_processor import (
    BatchProcessorService,
    BatchUploadRequest,
    BatchStatus,
    BatchJobPriority,
    BatchInfo,
    BatchFileInfo
)

class TestBatchProcessorService:
    """Test cases for BatchProcessorService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = BatchProcessorService()
        self.test_user_id = "test-user-123"
        
        # Mock database session
        self.mock_db = Mock()
        
        # Create test directory
        self.test_dir = Path("/tmp/test_batch_processor")
        self.test_dir.mkdir(exist_ok=True)
        
        # Patch storage directory to use test directory
        self.service.batch_storage_dir = self.test_dir
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def create_test_upload_file(self, filename: str, content: bytes, content_type: str = "audio/wav") -> UploadFile:
        """Create a test upload file."""
        file_obj = BytesIO(content)
        upload_file = UploadFile(
            filename=filename,
            file=file_obj,
            headers={"content-type": content_type}
        )
        upload_file.content_type = content_type
        return upload_file
    
    def test_create_batch_success(self):
        """Test successful batch creation."""
        # Create test files
        files = [
            self.create_test_upload_file("test1.wav", b"audio data 1"),
            self.create_test_upload_file("test2.wav", b"audio data 2")
        ]
        
        request = BatchUploadRequest(
            batch_name="Test Batch",
            description="Test batch description",
            model="small",
            auto_start=False
        )
        
        # Create batch
        batch_info = self.service.create_batch(
            db=self.mock_db,
            user_id=self.test_user_id,
            files=files,
            request=request
        )
        
        # Validate batch info
        assert batch_info.batch_name == "Test Batch"
        assert batch_info.user_id == self.test_user_id
        assert batch_info.total_files == 2
        assert batch_info.status == BatchStatus.PENDING.value
        assert len(batch_info.files) == 2
        
        # Check batch directory exists
        batch_dir = self.test_dir / batch_info.batch_id
        assert batch_dir.exists()
        
        # Check metadata file exists
        metadata_file = batch_dir / "batch_info.json"
        assert metadata_file.exists()
        
        # Check uploaded files exist
        for file_info in batch_info.files:
            file_path = batch_dir / file_info.filename
            assert file_path.exists()
    
    def test_create_batch_no_files(self):
        """Test batch creation with no files."""
        from fastapi import HTTPException
        
        request = BatchUploadRequest(batch_name="Empty Batch")
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.create_batch(
                db=self.mock_db,
                user_id=self.test_user_id,
                files=[],
                request=request
            )
        
        assert exc_info.value.status_code == 400
        assert "at least one file" in str(exc_info.value.detail).lower()
    
    def test_create_batch_too_many_files(self):
        """Test batch creation with too many files."""
        from fastapi import HTTPException
        
        # Create 51 files (exceeds limit of 50)
        files = []
        for i in range(51):
            files.append(self.create_test_upload_file(f"test{i}.wav", b"audio data"))
        
        request = BatchUploadRequest(batch_name="Large Batch")
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.create_batch(
                db=self.mock_db,
                user_id=self.test_user_id,
                files=files,
                request=request
            )
        
        assert exc_info.value.status_code == 400
        assert "maximum 50 files" in str(exc_info.value.detail).lower()
    
    def test_create_batch_file_too_large(self):
        """Test batch creation with file exceeding size limit."""
        from fastapi import HTTPException
        
        # Create file larger than 100MB
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        files = [self.create_test_upload_file("large.wav", large_content)]
        
        request = BatchUploadRequest(batch_name="Large File Batch")
        
        with pytest.raises(HTTPException) as exc_info:
            self.service.create_batch(
                db=self.mock_db,
                user_id=self.test_user_id,
                files=files,
                request=request
            )
        
        assert exc_info.value.status_code == 413
        assert "exceeds 100mb" in str(exc_info.value.detail).lower()
    
    def test_get_batch_info(self):
        """Test getting batch information."""
        # Create a batch first
        files = [self.create_test_upload_file("test.wav", b"audio data")]
        request = BatchUploadRequest(batch_name="Test Batch")
        
        batch_info = self.service.create_batch(
            db=self.mock_db,
            user_id=self.test_user_id,
            files=files,
            request=request
        )
        
        # Get batch info
        retrieved_info = self.service.get_batch_info(batch_info.batch_id)
        
        assert retrieved_info is not None
        assert retrieved_info.batch_id == batch_info.batch_id
        assert retrieved_info.batch_name == "Test Batch"
    
    def test_get_batch_info_not_found(self):
        """Test getting non-existent batch information."""
        result = self.service.get_batch_info("non-existent-batch")
        assert result is None
    
    def test_list_user_batches(self):
        """Test listing user batches."""
        # Create multiple batches
        for i in range(3):
            files = [self.create_test_upload_file(f"test{i}.wav", b"audio data")]
            request = BatchUploadRequest(batch_name=f"Batch {i}")
            
            self.service.create_batch(
                db=self.mock_db,
                user_id=self.test_user_id,
                files=files,
                request=request
            )
        
        # List batches
        batches = self.service.list_user_batches(self.test_user_id)
        
        assert len(batches) == 3
        assert all(batch.user_id == self.test_user_id for batch in batches)
        
        # Check ordering (newest first)
        batch_names = [batch.batch_name for batch in batches]
        assert batch_names == ["Batch 2", "Batch 1", "Batch 0"]
    
    def test_list_user_batches_with_pagination(self):
        """Test listing user batches with pagination."""
        # Create multiple batches
        for i in range(5):
            files = [self.create_test_upload_file(f"test{i}.wav", b"audio data")]
            request = BatchUploadRequest(batch_name=f"Batch {i}")
            
            self.service.create_batch(
                db=self.mock_db,
                user_id=self.test_user_id,
                files=files,
                request=request
            )
        
        # Test pagination
        page1 = self.service.list_user_batches(self.test_user_id, limit=2, offset=0)
        page2 = self.service.list_user_batches(self.test_user_id, limit=2, offset=2)
        
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].batch_name != page2[0].batch_name
    
    @pytest.mark.asyncio
    async def test_cancel_batch(self):
        """Test cancelling a batch."""
        # Create a batch
        files = [self.create_test_upload_file("test.wav", b"audio data")]
        request = BatchUploadRequest(batch_name="Test Batch")
        
        batch_info = self.service.create_batch(
            db=self.mock_db,
            user_id=self.test_user_id,
            files=files,
            request=request
        )
        
        # Cancel the batch
        success = await self.service.cancel_batch(batch_info.batch_id)
        
        assert success is True
        
        # Check status updated
        updated_info = self.service.get_batch_info(batch_info.batch_id)
        assert updated_info.status == BatchStatus.CANCELLED.value
        assert updated_info.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_batch(self):
        """Test cancelling a non-existent batch."""
        success = await self.service.cancel_batch("non-existent")
        assert success is False
    
    def test_cleanup_old_batches(self):
        """Test cleaning up old batches."""
        # Create test batch directory with old metadata
        old_batch_id = str(uuid.uuid4())
        old_batch_dir = self.test_dir / old_batch_id
        old_batch_dir.mkdir()
        
        # Create old metadata (35 days old)
        old_date = datetime.utcnow().replace(day=1)
        old_metadata = {
            "batch_id": old_batch_id,
            "created_at": old_date.isoformat(),
            "batch_name": "Old Batch"
        }
        
        metadata_file = old_batch_dir / "batch_info.json"
        with open(metadata_file, "w") as f:
            json.dump(old_metadata, f)
        
        # Run cleanup (30 day threshold)
        cleaned_count = self.service.cleanup_old_batches(days=30)
        
        assert cleaned_count >= 1
        assert not old_batch_dir.exists()

class TestBatchUploadRequest:
    """Test cases for BatchUploadRequest validation."""
    
    def test_valid_request(self):
        """Test valid batch upload request."""
        request = BatchUploadRequest(
            batch_name="Test Batch",
            description="Test description",
            model="medium",
            language="en",
            priority=BatchJobPriority.HIGH.value,
            auto_start=True,
            max_parallel_jobs=5
        )
        
        assert request.batch_name == "Test Batch"
        assert request.model == "medium"
        assert request.priority == BatchJobPriority.HIGH.value
        assert request.max_parallel_jobs == 5
    
    def test_invalid_batch_name(self):
        """Test invalid batch name."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            BatchUploadRequest(batch_name="")  # Empty name
    
    def test_invalid_max_parallel_jobs(self):
        """Test invalid max parallel jobs."""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            BatchUploadRequest(
                batch_name="Test",
                max_parallel_jobs=0  # Below minimum
            )
        
        with pytest.raises(ValidationError):
            BatchUploadRequest(
                batch_name="Test",
                max_parallel_jobs=15  # Above maximum
            )
    
    def test_default_values(self):
        """Test default values."""
        request = BatchUploadRequest(batch_name="Test")
        
        assert request.model == "small"
        assert request.priority == BatchJobPriority.NORMAL.value
        assert request.auto_start is True
        assert request.max_parallel_jobs == 3

if __name__ == "__main__":
    pytest.main([__file__])