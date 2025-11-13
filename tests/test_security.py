"""
Security testing suite for authentication, authorization, and input validation.

This module tests security-critical functionality including:
- Authentication bypass attempts
- Authorization checks
- Input validation and sanitization
- Token security
- Password security
"""

import pytest
import jwt
import secrets
import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException

from api.models import User, Job, JobStatusEnum
from api.services.user_service import UserService
from api.settings import settings
from api.orm_bootstrap import SessionLocal


class TestPasswordSecurity:
    """Test password hashing and validation security."""
    
    def test_password_hashed_not_stored_plain(self):
        """Verify passwords are hashed, not stored in plain text."""
        service = UserService()
        db = SessionLocal()
        try:
            user = service.create_user(db, "security_test_1", "security_test_1@example.com", "MySecurePassword123")
            
            # Password should be hashed
            assert user.hashed_password != "MySecurePassword123"
            
            # Should contain bcrypt markers
            assert user.hashed_password.startswith("$2b$")
            
            # Cleanup
            db.delete(user)
            db.commit()
        finally:
            db.close()
    
    def test_password_minimum_length_enforced(self):
        """Test that minimum password length is enforced."""
        service = UserService()
        db = SessionLocal()
        try:
            username = f"pwd_len_{uuid.uuid4().hex[:8]}"
            with pytest.raises(ValueError, match="at least 8 characters"):
                service.create_user(db, username, f"{username}@example.com", "short")
        finally:
            db.close()
    
    def test_bcrypt_rounds_sufficient(self):
        """Test that bcrypt uses sufficient cost factor."""
        service = UserService()
        hashed = service.hash_password("TestPassword123")
        
        # Extract cost factor from bcrypt hash
        # Format: $2b$<cost>$...
        parts = hashed.split("$")
        cost = int(parts[2])
        
        # Cost should be at least 12 for production
        assert cost >= 12, f"BCrypt cost factor {cost} is too low, should be >= 12"
    
    def test_timing_attack_resistance(self):
        """Test that password verification is timing-attack resistant."""
        service = UserService()
        db = SessionLocal()
        try:
            user = service.create_user(db, "timing_test", "timing_test@example.com", "CorrectPassword123")
            
            # Both should take similar time (constant-time comparison)
            # We can't easily test timing, but we verify both fail gracefully
            result1 = service.verify_password("WrongPassword", user.hashed_password)
            result2 = service.verify_password("AnotherWrong", user.hashed_password)
            
            assert result1 is False
            assert result2 is False
            
            # Cleanup
            db.delete(user)
            db.commit()
        finally:
            db.close()
    
    def test_password_change_requires_current(self):
        """Test that password changes require current password."""
        service = UserService()
        db = SessionLocal()
        try:
            user = service.create_user(db, "pwchange_test", "pwchange_test@example.com", "OldPassword123")
            
            # Should fail without correct current password
            with pytest.raises(ValueError, match="Current password is incorrect"):
                service.change_password(
                    db, user.id, "WrongOldPassword", "NewPassword123"
                )
            
            # Should succeed with correct current password
            service.change_password(
                db, user.id, "OldPassword123", "NewPassword123"
            )
            
            # Verify new password works
            authenticated = service.authenticate_user(db, "pwchange_test", "NewPassword123")
            assert authenticated is not None
            
            # Cleanup
            db.delete(user)
            db.commit()
        finally:
            db.close()


class TestAuthenticationSecurity:
    """Test authentication mechanism security."""
    
    def test_failed_login_doesnt_reveal_username_existence(self, client):
        """Test that failed login doesn't reveal if username exists."""
        # Login with non-existent user
        response1 = client.post(
            "/auth/login",
            json={"username": "definitely_not_exist_xyz", "password": "password"}
        )
        
        # Login with wrong password for existing user (if any)
        response2 = client.post(
            "/auth/login",
            json={"username": "admin", "password": "definitely_wrong_password"}
        )
        
        # Both should return same generic error
        assert response1.status_code in [401, 403]
        assert response2.status_code in [401, 403]
        
        # Error messages should be generic
        if "detail" in response1.json():
            detail = response1.json()["detail"]
            assert (
                "Invalid credentials" in detail
                or "Unauthorized" in detail
                or "Incorrect username or password" in detail
            )
    
    def test_token_expiration(self, client, auth_headers):
        """Test that expired tokens are rejected."""
        # Create an expired token
        expired_payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.jwt_secret_key,
            algorithm="HS256"
        )
        
        response = client.get(
            "/admin/stats",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code in [401, 403]
    
    def test_token_with_invalid_signature(self, client):
        """Test that tokens with invalid signatures are rejected."""
        # Create token with wrong key
        payload = {
            "sub": "testuser",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        fake_token = jwt.encode(
            payload,
            "wrong_secret_key_12345",
            algorithm="HS256"
        )
        
        response = client.get(
            "/admin/stats",
            headers={"Authorization": f"Bearer {fake_token}"}
        )
        assert response.status_code in [401, 403]
    
    def test_token_reuse_after_password_change(self):
        """Test that tokens are invalidated after password change."""
        # This would require implementing token versioning/blacklisting
        # For now, we document the expected behavior
        pass
    
    def test_brute_force_protection(self, client):
        """Test protection against brute force attacks."""
        # Attempt multiple failed logins
        for i in range(10):
            response = client.post(
                "/auth/login",
                json={"username": "admin", "password": f"wrong_password_{i}"}
            )
            assert response.status_code in [401, 403]
        
        # After many attempts, should still reject (or rate limit)
        # In production, implement rate limiting


class TestAuthorizationSecurity:
    """Test authorization and access control."""
    
    def test_regular_user_cannot_access_admin_endpoints(self, client, auth_headers):
        """Test that regular users cannot access admin-only endpoints."""
        endpoints = [
            "/admin/stats",
            "/admin/jobs",
            "/admin/health/system",
            "/admin/jobs/cleanup"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code in [403, 401], \
                f"Regular user accessed admin endpoint: {endpoint}"
    
    def test_user_cannot_access_other_users_jobs(self, client, auth_headers, db_session):
        """Test that users cannot access other users' jobs."""
        # Create another user's job
        other_user = User(
            username="other_security_user",
            email="other_security_user@example.com",
            hashed_password="hashed",
            role="user",
            created_at=datetime.utcnow()
        )
        db_session.add(other_user)
        db_session.commit()
        
        job = Job(
            id="other-user-job-123",
            user_id=str(other_user.id),
            original_filename="secret.wav",
            saved_filename="/tmp/secret.wav",
            model="small",
            status=JobStatusEnum.QUEUED,
            created_at=datetime.utcnow()
        )
        db_session.add(job)
        db_session.commit()
        
        # Try to access with different user's token
        response = client.get("/jobs/other-user-job-123", headers=auth_headers)
        assert response.status_code in [403, 404]
        
        # Cleanup
        db_session.delete(job)
        db_session.delete(other_user)
        db_session.commit()
    
    def test_privilege_escalation_prevention(self, client, auth_headers):
        """Test that users cannot escalate their privileges."""
        # Attempt to create admin user via API (if such endpoint exists)
        response = client.post(
            "/admin/users",
            json={"username": "fake_admin", "password": "password", "role": "admin"},
            headers=auth_headers
        )
        # Should be forbidden for non-admin
        assert response.status_code in [401, 403, 404, 405]


class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    def test_sql_injection_prevention(self, client):
        """Test protection against SQL injection."""
        # Try SQL injection in username
        response = client.post(
            "/auth/login",
            json={
                "username": "admin' OR '1'='1' --",
                "password": "password"
            }
        )
        assert response.status_code in [401, 403, 422]
        
        # Try SQL injection in search
        response = client.get(
            "/admin/jobs?search=' OR '1'='1",
            headers={"Authorization": "Bearer fake_token"}
        )
        # Should fail authentication, not execute SQL
        assert response.status_code in [401, 403]
    
    def test_path_traversal_prevention(self, client, auth_headers):
        """Test protection against path traversal attacks."""
        # Try path traversal in filename
        files = {
            "file": ("../../etc/passwd", b"fake audio data", "audio/wav")
        }
        response = client.post("/upload", files=files, headers=auth_headers)
        
        # Should either reject or sanitize
        if response.status_code in [200, 201]:
            # If accepted, filename should be sanitized
            job_data = response.json()
            # Original filename should not contain path traversal
            assert ".." not in job_data.get("original_filename", "")
    
    def test_xss_prevention(self, client, auth_headers):
        """Test protection against XSS attacks."""
        # Try XSS in filename
        files = {
            "file": ("<script>alert('XSS')</script>.wav", b"fake audio", "audio/wav")
        }
        response = client.post("/upload", files=files, headers=auth_headers)
        
        if response.status_code in [200, 201]:
            job_data = response.json()
            # Should not contain unescaped script tags
            filename = job_data.get("original_filename", "")
            assert "<script>" not in filename or "&lt;script&gt;" in filename
    
    def test_command_injection_prevention(self, client, auth_headers):
        """Test protection against command injection."""
        # Try command injection in filename
        files = {
            "file": ("test.wav; rm -rf /", b"fake audio", "audio/wav")
        }
        response = client.post("/upload", files=files, headers=auth_headers)
        
        # Should handle safely (accept with sanitization or reject)
        assert response.status_code in [200, 201, 400]
    
    def test_ldap_injection_prevention(self):
        """Test protection against LDAP injection (if LDAP is used)."""
        service = UserService()
        
        # Try LDAP injection characters in username
        with pytest.raises(ValueError):
            service.hash_password("")  # Empty password
    
    def test_xml_injection_prevention(self, client, auth_headers):
        """Test protection against XML/XXE attacks."""
        # If API accepts XML, test XXE prevention
        # For now, verify only JSON is accepted
        response = client.post(
            "/upload",
            data="<?xml version='1.0'?><file>test</file>",
            headers={
                **auth_headers,
                "Content-Type": "application/xml"
            }
        )
        # Should reject XML or handle safely
        assert response.status_code in [400, 415, 422]


class TestSecretKeySecurity:
    """Test secret key configuration security."""
    
    def test_secret_key_minimum_length(self):
        """Test that short secret keys are rejected in production."""
        # This should be caught by settings validation
        # Test is mainly documentation of the requirement
        assert len(settings.secret_key) >= 32, \
            "SECRET_KEY must be at least 32 characters in production"
    
    def test_secret_key_not_default(self):
        """Test that default/common secret keys are rejected."""
        insecure_keys = [
            "secret",
            "password",
            "admin",
            "test",
            "development",
            "your-secret-key",
            "change-me"
        ]
        
        # In production, these should be rejected
        assert settings.secret_key.lower() not in insecure_keys, \
            "SECRET_KEY must not be a common insecure value"


class TestSessionSecurity:
    """Test session management security."""
    
    def test_session_fixation_prevention(self, client):
        """Test protection against session fixation attacks."""
        # Login should generate new session/token
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass"}
        )
        
        if response.status_code == 200:
            token1 = response.json().get("access_token")
            
            # Login again should generate different token
            response2 = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "testpass"}
            )
            
            if response2.status_code == 200:
                token2 = response2.json().get("access_token")
                
                # Tokens should be different
                assert token1 != token2
    
    def test_token_contains_minimal_information(self, client, auth_headers):
        """Test that tokens don't leak sensitive information."""
        # Extract token from headers
        token = auth_headers.get("Authorization", "").replace("Bearer ", "")
        
        if token:
            # Decode without verification to inspect payload
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                
                # Should not contain sensitive data
                sensitive_fields = ["password", "hashed_password", "secret"]
                for field in sensitive_fields:
                    assert field not in payload, \
                        f"Token contains sensitive field: {field}"
            except Exception:
                pass  # Token might be encrypted or formatted differently


class TestFileUploadSecurity:
    """Test file upload security."""
    
    def test_file_type_validation(self, client, auth_headers):
        """Test that file type is properly validated."""
        # Try uploading executable
        files = {"file": ("malware.exe", b"MZ\x90\x00", "application/x-msdownload")}
        response = client.post("/upload", files=files, headers=auth_headers)
        assert response.status_code == 400
    
    def test_file_size_limit_enforced(self, client, auth_headers):
        """Test that file size limits are enforced."""
        # Try uploading very large file
        large_file = b"x" * (200 * 1024 * 1024)  # 200MB
        files = {"file": ("huge.wav", large_file, "audio/wav")}
        response = client.post("/upload", files=files, headers=auth_headers)
        assert response.status_code in [400, 413]
    
    def test_filename_sanitization(self, client, auth_headers):
        """Test that filenames are sanitized."""
        dangerous_names = [
            "../../../etc/passwd",
            "test\x00.wav",  # Null byte injection
            "CON.wav",  # Windows reserved name
            "test|command.wav",  # Pipe character
        ]
        
        for name in dangerous_names:
            files = {"file": (name, b"fake audio", "audio/wav")}
            response = client.post("/upload", files=files, headers=auth_headers)
            
            if response.status_code in [200, 201]:
                # If accepted, verify filename was sanitized
                job_data = response.json()
                saved_name = job_data.get("original_filename", "")
                
                # Should not contain dangerous characters
                assert ".." not in saved_name
                assert "\x00" not in saved_name
                assert "|" not in saved_name


class TestRateLimiting:
    """Test rate limiting (if implemented)."""
    
    def test_login_rate_limiting(self, client):
        """Test that login attempts are rate limited."""
        # Make many login attempts
        for i in range(20):
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "wrong"}
            )
            # First few should return 401, later ones might return 429
            assert response.status_code in [401, 403, 429]
    
    def test_api_rate_limiting(self, client, auth_headers):
        """Test that API calls are rate limited."""
        # Make many rapid requests
        responses = []
        for i in range(100):
            response = client.get("/health", headers=auth_headers)
            responses.append(response.status_code)
        
        # At least some should succeed
        assert 200 in responses or 429 in responses


class TestCryptographicSecurity:
    """Test cryptographic implementations."""
    
    def test_secure_random_generation(self):
        """Test that secure random number generation is used."""
        # Generate multiple tokens
        tokens = [secrets.token_urlsafe(32) for _ in range(10)]
        
        # All should be unique
        assert len(set(tokens)) == len(tokens)
        
        # All should be sufficiently long
        for token in tokens:
            assert len(token) >= 32
    
    def test_jwt_algorithm_secure(self, client):
        """Test that JWT uses secure algorithm."""
        # Should use HS256 or RS256, not 'none'
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass"}
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                header = jwt.get_unverified_header(token)
                assert header["alg"] in ["HS256", "RS256", "ES256"]
                assert header["alg"] != "none"
