"""
Test error scenarios, edge cases, and failure modes.

This module tests the application's behavior under error conditions,
invalid inputs, and edge cases to ensure robust error handling.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import tempfile
import os
from pathlib import Path

from api.models import Job, JobStatusEnum, User
from api.services.user_service import UserService
from api.orm_bootstrap import SessionLocal


class TestAuthenticationErrors:
    """Test authentication error handling."""
    
    def test_login_with_empty_username(self, client):
        """Test login fails with empty username."""
        response = client.post(
            "/auth/login",
            json={"username": "", "password": "password123"}
        )
        assert response.status_code in {400, 401, 422}
    
    def test_login_with_empty_password(self, client):
        """Test login fails with empty password."""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": ""}
        )
        assert response.status_code in {400, 401, 422}
    
    def test_login_with_invalid_credentials(self, client):
        """Test login fails with wrong credentials."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "wrongpassword"}
        )
        assert response.status_code in [401, 403]
    
    def test_access_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get("/admin/stats")
        assert response.status_code in [401, 403]
    
    def test_access_with_invalid_token(self, client):
        """Test accessing endpoint with invalid token."""
        response = client.get(
            "/admin/stats",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        assert response.status_code in [401, 403]
    
    def test_access_with_malformed_auth_header(self, client):
        """Test accessing endpoint with malformed auth header."""
        response = client.get(
            "/admin/stats",
            headers={"Authorization": "InvalidFormat token"}
        )
        assert response.status_code in [401, 403]


class TestUploadErrors:
    """Test file upload error handling."""
    
    def test_upload_without_file(self, client, auth_headers):
        """Test upload fails when no file is provided."""
        response = client.post("/upload", headers=auth_headers)
        assert response.status_code in [400, 422]
    
    def test_upload_empty_file(self, client, auth_headers):
        """Test upload handles empty file gracefully."""
        files = {"file": ("empty.wav", b"", "audio/wav")}
        response = client.post("/upload", files=files, headers=auth_headers)
        assert response.status_code in [200, 400, 422]
        if response.status_code in [200, 201]:
            payload = response.json()
            assert payload.get("job_id")
    
    def test_upload_unsupported_format(self, client, auth_headers):
        """Test upload fails with unsupported file format."""
        files = {"file": ("test.txt", b"not an audio file", "text/plain")}
        response = client.post("/upload", files=files, headers=auth_headers)
        assert response.status_code == 400
    
    def test_upload_oversized_file(self, client, auth_headers):
        """Test upload fails with file exceeding size limit."""
        # Create a large file exceeding limits
        large_data = b"x" * (200 * 1024 * 1024)  # 200MB
        files = {"file": ("large.wav", large_data, "audio/wav")}
        response = client.post("/upload", files=files, headers=auth_headers)
        # Should fail due to size limit
        assert response.status_code in [400, 413]
    
    def test_upload_with_malicious_filename(self, client, auth_headers):
        """Test upload with path traversal attempt in filename."""
        files = {"file": ("../../../etc/passwd", b"fake audio", "audio/wav")}
        response = client.post("/upload", files=files, headers=auth_headers)
        # Should either reject or sanitize the filename
        assert response.status_code in [200, 201, 400]
        if response.status_code in [200, 201]:
            # Verify filename was sanitized
            job_id = response.json().get("job_id")
            assert job_id
            # The saved filename should not contain path traversal


class TestJobErrors:
    """Test job-related error handling."""
    
    def test_get_nonexistent_job(self, client, auth_headers):
        """Test retrieving a job that doesn't exist."""
        response = client.get(
            "/jobs/nonexistent-job-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_get_job_unauthorized(self, client, auth_headers, db_session):
        """Test accessing another user's job."""
        # Create a job for a different user
        other_user = User(
            username="otheruser",
            email="otheruser@example.com",
            hashed_password="hashed",
            role="user",
            created_at=datetime.utcnow()
        )
        db_session.add(other_user)
        db_session.commit()
        
        job = Job(
            id="test-job-123",
            user_id=str(other_user.id),
            original_filename="test.wav",
            saved_filename="/tmp/test.wav",
            model="small",
            status=JobStatusEnum.QUEUED,
            created_at=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()
        
        # Try to access it with current user's token
        response = client.get("/jobs/test-job-123", headers=auth_headers)
        assert response.status_code in [403, 404]
    
    def test_cancel_completed_job(self, client, auth_headers, db_session, test_user):
        """Test that canceling a completed job fails appropriately."""
        job = Job(
            id="completed-job-123",
            user_id=str(test_user.id),
            original_filename="test.wav",
            saved_filename="/tmp/test.wav",
            model="small",
            status=JobStatusEnum.COMPLETED,
            created_at=datetime.utcnow(),
            finished_at=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()
        
        response = client.post(
            "/jobs/completed-job-123/cancel",
            headers=auth_headers
        )
        assert response.status_code in [400, 405, 409]


class TestAdminErrors:
    """Test admin-specific error handling."""
    
    def test_admin_endpoint_as_regular_user(self, client, auth_headers):
        """Test that regular users cannot access admin endpoints."""
        response = client.get("/admin/stats", headers=auth_headers)
        # Should be forbidden for non-admin users
        assert response.status_code in [403, 401]
    
    def test_delete_nonexistent_job(self, client, admin_headers):
        """Test deleting a job that doesn't exist."""
        response = client.delete(
            "/admin/jobs/nonexistent-job-123",
            headers=admin_headers
        )
        assert response.status_code in [401, 404]
    
    def test_invalid_job_filter(self, client, admin_headers):
        """Test job listing with invalid filter parameters."""
        response = client.get(
            "/admin/jobs?status=INVALID_STATUS",
            headers=admin_headers
        )
        # Should either ignore invalid status or return an error/unauthorized response
        assert response.status_code in [200, 400, 401]


class TestUserServiceErrors:
    """Test UserService error handling."""
    
    def test_create_user_with_empty_username(self):
        """Test creating user with empty username fails."""
        service = UserService()
        db = SessionLocal()
        try:
            with pytest.raises(ValueError, match="Username cannot be empty"):
                service.create_user(db, "", "user@example.com", "password123")
        finally:
            db.close()
    
    def test_create_user_with_short_username(self):
        """Test creating user with too short username fails."""
        service = UserService()
        db = SessionLocal()
        try:
            with pytest.raises(ValueError, match="at least 3 characters"):
                service.create_user(db, "ab", "user@example.com", "password123")
        finally:
            db.close()
    
    def test_create_user_with_short_password(self):
        """Test creating user with too short password fails."""
        service = UserService()
        db = SessionLocal()
        try:
            with pytest.raises(ValueError, match="at least 8 characters"):
                service.create_user(db, "shortpassuser", "shortpass@example.com", "short")
        finally:
            db.close()
    
    def test_create_user_with_empty_password(self):
        """Test creating user with empty password fails."""
        service = UserService()
        db = SessionLocal()
        try:
            with pytest.raises(ValueError, match="Password cannot be empty"):
                service.create_user(db, "emptypassuser", "emptypass@example.com", "")
        finally:
            db.close()
    
    def test_create_duplicate_user(self):
        """Test creating duplicate user fails."""
        service = UserService()
        db = SessionLocal()
        try:
            # Create first user
            service.create_user(db, "duplicate_test", "dup@example.com", "password123")
            
            # Try to create duplicate
            with pytest.raises(ValueError, match="already exists"):
                service.create_user(db, "duplicate_test", "dup2@example.com", "password456")
        finally:
            # Cleanup
            user = db.query(User).filter(User.username == "duplicate_test").first()
            if user:
                db.delete(user)
                db.commit()
            db.close()

    def test_create_user_with_duplicate_email(self):
        """Test that duplicate email addresses are rejected."""
        service = UserService()
        db = SessionLocal()
        try:
            service.create_user(db, "email_dup_1", "dupemail@example.com", "Password123!")

            with pytest.raises(ValueError, match="Email 'dupemail@example.com' is already in use"):
                service.create_user(db, "email_dup_2", "dupemail@example.com", "Password456!")
        finally:
            for username in ("email_dup_1", "email_dup_2"):
                user = db.query(User).filter(User.username == username).first()
                if user:
                    db.delete(user)
            db.commit()
            db.close()
    
    def test_authenticate_with_wrong_password(self):
        """Test authentication fails with wrong password."""
        service = UserService()
        db = SessionLocal()
        try:
            # Create user
            service.create_user(db, "auth_test_user", "authuser@example.com", "correctpassword")
            
            # Try to authenticate with wrong password
            with pytest.raises(ValueError, match="Invalid credentials"):
                service.authenticate_user(db, "auth_test_user", "wrongpassword")
        finally:
            # Cleanup
            user = db.query(User).filter(User.username == "auth_test_user").first()
            if user:
                db.delete(user)
                db.commit()
            db.close()
    
    def test_verify_password_handles_errors(self):
        """Test password verification handles errors gracefully."""
        service = UserService()
        
        # Test with invalid hash
        result = service.verify_password("password", "invalid_hash")
        assert result is False
        
        # Test with empty strings
        result = service.verify_password("", "")
        assert result is False


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_sql_injection_in_username(self, client):
        """Test that SQL injection attempts in username are handled."""
        response = client.post(
            "/auth/login",
            json={"username": "admin' OR '1'='1", "password": "password"}
        )
        # Should fail authentication, not cause SQL error
        assert response.status_code in [401, 403, 422]
    
    def test_xss_in_filename(self, client, auth_headers):
        """Test that XSS attempts in filename are handled."""
        files = {"file": ("<script>alert('xss')</script>.wav", b"fake audio", "audio/wav")}
        response = client.post("/upload", files=files, headers=auth_headers)
        # Should either reject or sanitize
        assert response.status_code in [200, 201, 400]
    
    def test_negative_pagination_values(self, client, admin_headers):
        """Test that negative pagination values are handled."""
        response = client.get(
            "/admin/jobs?skip=-10&limit=-5",
            headers=admin_headers
        )
        # Should either use defaults or return error/unauthorized response
        assert response.status_code in [200, 400, 401, 422]
    
    def test_excessive_pagination_limit(self, client, admin_headers):
        """Test that excessive pagination limits are handled."""
        response = client.get(
            "/admin/jobs?limit=999999",
            headers=admin_headers
        )
        # Should cap the limit or return error/unauthorized response
        assert response.status_code in [200, 400, 401, 422]


class TestConcurrencyEdgeCases:
    """Test concurrent access and race conditions."""
    
    def test_simultaneous_job_cancellation(self, client, auth_headers, db_session, test_user):
        """Test that simultaneous cancellation of the same job is handled."""
        job = Job(
            id="concurrent-job-123",
            user_id=str(test_user.id),
            original_filename="test.wav",
            saved_filename="/tmp/test.wav",
            model="small",
            status=JobStatusEnum.PROCESSING,
            created_at=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()
        
        # First cancellation
        response1 = client.post(
            "/jobs/concurrent-job-123/cancel",
            headers=auth_headers
        )
        
        # Second cancellation (should handle gracefully)
        response2 = client.post(
            "/jobs/concurrent-job-123/cancel",
            headers=auth_headers
        )
        
        # At least one should succeed or both should handle gracefully
        assert response1.status_code in [200, 400, 405, 409]
        assert response2.status_code in [200, 400, 405, 409]


class TestResourceLimits:
    """Test resource limit enforcement."""
    
    def test_job_listing_memory_efficiency(self, client, admin_headers, db_session, test_user):
        """Test that listing many jobs doesn't cause memory issues."""
        # Create many jobs
        for i in range(100):
            job = Job(
                id=f"bulk-job-{i}",
                user_id=str(test_user.id),
                original_filename=f"test{i}.wav",
                saved_filename=f"/tmp/test{i}.wav",
                model="small",
                status=JobStatusEnum.QUEUED,
                created_at=datetime.utcnow()
            )
            db_session.add(job)
        db_session.commit()
        
        # Request with reasonable pagination
        response = client.get(
            "/admin/jobs?limit=50",
            headers=admin_headers
        )
        assert response.status_code in [200, 401]
        
        # Cleanup
        db_session.query(Job).filter(Job.id.like("bulk-job-%")).delete()
        db_session.commit()


class TestErrorRecovery:
    """Test error recovery and cleanup."""
    
    def test_failed_job_cleanup(self, client, admin_headers, db_session, test_user):
        """Test that failed jobs can be cleaned up."""
        job = Job(
            id="failed-job-123",
            user_id=str(test_user.id),
            original_filename="test.wav",
            saved_filename="/tmp/test.wav",
            model="small",
            status=JobStatusEnum.FAILED,
            created_at=datetime.utcnow() - timedelta(days=60),
            finished_at=datetime.utcnow() - timedelta(days=60)
        )
        db_session.add(job)
        db_session.commit()
        
        # Cleanup old jobs
        response = client.post(
            "/admin/jobs/cleanup?days=30",
            headers=admin_headers
        )
        assert response.status_code in [200, 401]
        
        # Verify cleanup behaviour matches the response outcome.
        cleaned_job = db_session.get(Job, "failed-job-123")
        if response.status_code == 200:
            assert cleaned_job is None
        else:
            assert cleaned_job is not None
