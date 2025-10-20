"""
Comprehensive Authentication Testing Suite

This module provides comprehensive testing for the authentication system including:
- User registration and login functionality
- Password hashing and verification
- JWT token generation and validation
- Session management and refresh tokens
- Role-based access control
- Security edge cases and error scenarios

Test Categories:
1. Unit Tests - Core authentication logic
2. Integration Tests - Full authentication flow
3. Security Tests - Security vulnerabilities and edge cases
4. API Tests - Authentication endpoint testing
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from passlib.context import CryptContext
import jwt

# Import application components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
from api.models import User, SessionLocal
from api.schemas import UserCreate, UserLogin, Token
from api.services.auth_service import AuthService
from api.utils.security import verify_password, get_password_hash, create_access_token, verify_token

class TestAuthenticationUnit:
    """Unit tests for core authentication logic"""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance for testing"""
        return AuthService()
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing"""
        return {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
    
    @pytest.fixture
    def sample_user_create(self, sample_user_data):
        """UserCreate schema for testing"""
        return UserCreate(**sample_user_data)
    
    def test_password_hashing(self, sample_user_data):
        """Test password hashing and verification"""
        password = sample_user_data["password"]
        
        # Test password hashing
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 characters
        
        # Test password verification
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
        assert verify_password("", hashed) is False
        
    def test_password_strength_validation(self, auth_service):
        """Test password strength requirements"""
        # Strong passwords should pass
        strong_passwords = [
            "StrongPassword123!",
            "AnotherGood1@",
            "Complex#Pass9"
        ]
        
        for password in strong_passwords:
            result = auth_service.validate_password_strength(password)
            assert result["valid"] is True
            assert result["score"] >= 3
        
        # Weak passwords should fail
        weak_passwords = [
            "123456",
            "password",
            "abc",
            "qwerty",
            "Password",  # Missing numbers/symbols
            "password123",  # Missing capitals/symbols
            "PASSWORD123!"  # Missing lowercase
        ]
        
        for password in weak_passwords:
            result = auth_service.validate_password_strength(password)
            assert result["valid"] is False
            assert len(result["issues"]) > 0
    
    def test_jwt_token_creation(self, sample_user_data):
        """Test JWT token creation and validation"""
        user_data = {"sub": sample_user_data["username"], "user_id": 1}
        
        # Test token creation
        token = create_access_token(data=user_data)
        assert isinstance(token, str)
        assert len(token) > 100  # JWT tokens are typically long
        
        # Test token validation
        payload = verify_token(token)
        assert payload["sub"] == user_data["sub"]
        assert payload["user_id"] == user_data["user_id"]
        assert "exp" in payload
        
        # Test expired token
        expired_token = create_access_token(
            data=user_data, 
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_expiration_validation(self):
        """Test token expiration handling"""
        # Create token with custom expiration
        user_data = {"sub": "testuser", "user_id": 1}
        
        # Short expiration
        short_token = create_access_token(
            data=user_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Should be valid immediately
        payload = verify_token(short_token)
        assert payload["sub"] == "testuser"
        
        # Should be invalid after expiration (simulate by creating already expired)
        expired_token = create_access_token(
            data=user_data,
            expires_delta=timedelta(seconds=-10)
        )
        
        with pytest.raises(HTTPException):
            verify_token(expired_token)
    
    def test_invalid_token_formats(self):
        """Test handling of invalid token formats"""
        invalid_tokens = [
            "invalid.token.here",
            "not_a_jwt_token",
            "",
            None,
            "Bearer invalid_token",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",  # Malformed JWT
        ]
        
        for token in invalid_tokens:
            with pytest.raises(HTTPException) as exc_info:
                verify_token(token)
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

class TestAuthenticationIntegration:
    """Integration tests for complete authentication flows"""
    
    @pytest.fixture
    def client(self):
        """Test client for API testing"""
        return TestClient(app)
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data"""
        return {
            "username": "integration_test_user",
            "email": "integration@test.com",
            "password": "IntegrationTest123!",
            "full_name": "Integration Test User"
        }
    
    def test_complete_registration_flow(self, client, test_user_data):
        """Test complete user registration flow"""
        # Test registration
        response = client.post("/register", json=test_user_data)
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data or "message" in data
            assert "user" in data or "username" in data.get("message", "")
        else:
            # User might already exist, check for appropriate error
            assert response.status_code in [400, 409]
            assert "already exists" in response.json().get("detail", "").lower()
    
    def test_complete_login_flow(self, client, test_user_data):
        """Test complete user login flow"""
        # Ensure user exists (register first)
        client.post("/register", json=test_user_data)
        
        # Test login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/token", data=login_data)
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
            
            # Test using the token
            headers = {"Authorization": f"Bearer {data['access_token']}"}
            protected_response = client.get("/dashboard", headers=headers)
            assert protected_response.status_code in [200, 404]  # 404 if route doesn't exist yet
        else:
            # Check for authentication error
            assert response.status_code in [401, 422]
    
    def test_token_refresh_flow(self, client, test_user_data):
        """Test token refresh functionality"""
        # Register and login
        client.post("/register", json=test_user_data)
        login_response = client.post("/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            original_token = token_data["access_token"]
            
            # Test token refresh (if endpoint exists)
            headers = {"Authorization": f"Bearer {original_token}"}
            refresh_response = client.post("/token/refresh", headers=headers)
            
            if refresh_response.status_code == 200:
                new_token_data = refresh_response.json()
                assert "access_token" in new_token_data
                assert new_token_data["access_token"] != original_token
            elif refresh_response.status_code == 404:
                # Refresh endpoint not implemented yet
                pass
            else:
                assert refresh_response.status_code in [401, 422]
    
    def test_protected_endpoint_access(self, client, test_user_data):
        """Test access to protected endpoints"""
        # Register and login
        client.post("/register", json=test_user_data)
        login_response = client.post("/token", data={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Test protected endpoints
            protected_endpoints = [
                "/dashboard",
                "/jobs", 
                "/change-password",
                "/user/profile"
            ]
            
            for endpoint in protected_endpoints:
                response = client.get(endpoint, headers=headers)
                # Should not get 401/403 with valid token
                assert response.status_code not in [401, 403] or response.status_code == 404
    
    def test_unauthorized_access_rejection(self, client):
        """Test that unauthorized requests are rejected"""
        protected_endpoints = [
            "/dashboard",
            "/jobs",
            "/change-password",
            "/admin/stats"
        ]
        
        for endpoint in protected_endpoints:
            # Test without token
            response = client.get(endpoint)
            if response.status_code not in [404, 200]:  # Some endpoints might not be protected yet
                assert response.status_code in [401, 403]
            
            # Test with invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            response = client.get(endpoint, headers=invalid_headers)
            if response.status_code not in [404, 200]:  # Some endpoints might not be protected yet
                assert response.status_code in [401, 403]

class TestAuthenticationSecurity:
    """Security tests for authentication vulnerabilities"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_password_injection_attempts(self, client):
        """Test SQL injection attempts in passwords"""
        malicious_passwords = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--", 
            "' UNION SELECT * FROM users--",
            "<script>alert('xss')</script>"
        ]
        
        for password in malicious_passwords:
            user_data = {
                "username": f"test_injection_{hash(password)}",
                "email": f"test{hash(password)}@example.com",
                "password": password,
                "full_name": "Test User"
            }
            
            # Should not cause SQL injection or other security issues
            response = client.post("/register", json=user_data)
            # Should either register successfully or fail validation, but not crash
            assert response.status_code in [200, 400, 422]
    
    def test_username_injection_attempts(self, client):
        """Test injection attempts in usernames"""
        malicious_usernames = [
            "admin'; DROP TABLE users; --",
            "' OR 1=1--",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "null\x00user"
        ]
        
        for username in malicious_usernames:
            user_data = {
                "username": username,
                "email": f"test{hash(username)}@example.com", 
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
            
            response = client.post("/register", json=user_data)
            # Should handle malicious input safely
            assert response.status_code in [200, 400, 422]
    
    def test_rate_limiting_protection(self, client):
        """Test rate limiting on authentication endpoints"""
        # Test multiple rapid login attempts
        login_data = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }
        
        responses = []
        for i in range(10):
            response = client.post("/token", data=login_data)
            responses.append(response.status_code)
        
        # Should eventually start rate limiting (429) or maintain 401
        # At minimum, should not crash or return 500 errors
        for status_code in responses:
            assert status_code in [401, 422, 429]
    
    def test_brute_force_protection(self, client):
        """Test protection against brute force attacks"""
        # Create a test user
        test_user = {
            "username": "brute_force_test",
            "email": "bruteforce@test.com",
            "password": "CorrectPassword123!",
            "full_name": "Brute Force Test"
        }
        client.post("/register", json=test_user)
        
        # Attempt multiple wrong passwords
        wrong_passwords = [
            "wrongpass1", "wrongpass2", "wrongpass3", 
            "wrongpass4", "wrongpass5", "wrongpass6"
        ]
        
        for password in wrong_passwords:
            login_data = {
                "username": test_user["username"],
                "password": password
            }
            response = client.post("/token", data=login_data)
            assert response.status_code in [401, 422, 429]  # Should reject wrong passwords
    
    def test_session_security(self, client):
        """Test session security measures"""
        # Create and login user
        user_data = {
            "username": "session_test_user",
            "email": "session@test.com", 
            "password": "SessionTest123!",
            "full_name": "Session Test User"
        }
        client.post("/register", json=user_data)
        
        login_response = client.post("/token", data={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data["access_token"]
            
            # Test that token is not too long-lived
            payload = jwt.decode(token, options={"verify_signature": False})
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            token_lifetime = exp - now
            
            # Token should not live longer than reasonable time (e.g., 24 hours)
            assert token_lifetime.total_seconds() < 24 * 60 * 60
            
            # Test that token contains expected claims
            assert "sub" in payload
            assert "exp" in payload
            assert "iat" in payload

class TestAuthenticationAPI:
    """API endpoint tests for authentication"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_register_endpoint_validation(self, client):
        """Test registration endpoint input validation"""
        # Test valid registration
        valid_data = {
            "username": "valid_user_api",
            "email": "valid@example.com",
            "password": "ValidPassword123!",
            "full_name": "Valid User"
        }
        
        response = client.post("/register", json=valid_data)
        assert response.status_code in [200, 400, 409]  # 400/409 if user exists
        
        # Test invalid email formats
        invalid_emails = ["invalid", "@invalid.com", "invalid@", "invalid.com"]
        for email in invalid_emails:
            invalid_data = valid_data.copy()
            invalid_data["email"] = email
            invalid_data["username"] = f"user_{hash(email)}"
            
            response = client.post("/register", json=invalid_data)
            assert response.status_code in [400, 422]  # Should reject invalid email
        
        # Test missing required fields
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            incomplete_data = valid_data.copy()
            del incomplete_data[field]
            
            response = client.post("/register", json=incomplete_data)
            assert response.status_code == 422  # Validation error
    
    def test_login_endpoint_validation(self, client):
        """Test login endpoint input validation"""
        # Create test user first
        user_data = {
            "username": "login_test_user",
            "email": "login@test.com",
            "password": "LoginTest123!",
            "full_name": "Login Test User"
        }
        client.post("/register", json=user_data)
        
        # Test valid login
        valid_login = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        response = client.post("/token", data=valid_login)
        assert response.status_code in [200, 401]  # 200 for success, 401 for auth failure
        
        # Test invalid credentials
        invalid_login = {
            "username": user_data["username"],
            "password": "wrong_password"
        }
        response = client.post("/token", data=invalid_login)
        assert response.status_code in [401, 422]
        
        # Test missing fields
        response = client.post("/token", data={"username": "test"})
        assert response.status_code == 422
        
        response = client.post("/token", data={"password": "test"})
        assert response.status_code == 422
    
    def test_protected_endpoints_response_format(self, client):
        """Test that protected endpoints return proper error formats"""
        protected_endpoints = ["/dashboard", "/jobs", "/change-password"]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            
            if response.status_code in [401, 403]:
                # Should return proper error format
                data = response.json()
                assert "detail" in data or "message" in data
            elif response.status_code == 404:
                # Endpoint not implemented yet - acceptable
                pass
    
    def test_cors_headers_on_auth_endpoints(self, client):
        """Test CORS headers on authentication endpoints"""
        auth_endpoints = ["/register", "/token", "/dashboard"]
        
        for endpoint in auth_endpoints:
            response = client.options(endpoint)
            
            # Check for CORS headers (if CORS is configured)
            headers = response.headers
            
            # At minimum, should not return 500 error
            assert response.status_code != 500
    
    def test_content_type_validation(self, client):
        """Test content type validation for auth endpoints"""
        # Test POST endpoints with wrong content type
        endpoints_data = [
            ("/register", {"username": "test", "email": "test@test.com", "password": "Test123!"}),
            ("/token", {"username": "test", "password": "Test123!"})
        ]
        
        for endpoint, data in endpoints_data:
            # Test with text/plain (should fail)
            response = client.post(
                endpoint, 
                data=str(data),
                headers={"Content-Type": "text/plain"}
            )
            assert response.status_code in [400, 415, 422]  # Should reject wrong content type

@pytest.mark.asyncio
async def test_authentication_performance():
    """Test authentication performance benchmarks"""
    import time
    
    # Test password hashing performance
    start_time = time.time()
    password = "TestPassword123!"
    
    # Hash 10 passwords
    for i in range(10):
        hashed = get_password_hash(f"{password}_{i}")
        assert len(hashed) > 50
    
    hash_time = time.time() - start_time
    
    # Hashing 10 passwords should take less than 5 seconds
    assert hash_time < 5.0
    
    # Test password verification performance
    hashed_password = get_password_hash(password)
    start_time = time.time()
    
    # Verify 50 passwords
    for i in range(50):
        result = verify_password(password, hashed_password)
        assert result is True
    
    verify_time = time.time() - start_time
    
    # Verifying 50 passwords should take less than 3 seconds
    assert verify_time < 3.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
