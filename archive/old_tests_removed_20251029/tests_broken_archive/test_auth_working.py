"""
Working Authentication Tests

Simple authentication tests that work with the current implementation.
"""

import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Import application components
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
from api.routes.auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    verify_token,
    USERS_DB,
    SECRET_KEY,
    ALGORITHM
)

# Test client
client = TestClient(app)


class TestBasicAuth:
    """Test basic authentication functionality."""
    
    def test_password_hashing(self):
        """Test password hashing function."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Should return a hex string of expected length (SHA256)
        assert isinstance(hashed, str)
        assert len(hashed) == 64
        
        # Same password should produce same hash
        assert hash_password(password) == hashed
        
    def test_password_verification(self):
        """Test password verification."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        
        # Wrong password should not verify
        assert verify_password("wrong_password", hashed) is False
        
    def test_jwt_token_creation(self):
        """Test JWT token creation."""
        data = {"sub": "admin"}
        token = create_access_token(data)
        
        # Should return a JWT token string
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Token should be decodable
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "admin"
        assert "exp" in decoded
        
    def test_jwt_token_expiry(self):
        """Test JWT token with custom expiry."""
        data = {"sub": "admin"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        expected_time = datetime.utcnow() + expires_delta
        
        # Should be within a few seconds of expected time
        time_diff = abs((exp_time - expected_time).total_seconds())
        assert time_diff < 5


class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_login_success(self):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "password"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong_password"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
        
    def test_login_wrong_username(self):
        """Test login with wrong username."""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
        
    def test_get_current_user(self):
        """Test getting current user info."""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "password"}
        )
        token = login_response.json()["access_token"]
        
        # Use token to get user info
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["username"] == "admin"
        assert data["is_active"] is True
        assert "id" in data
        
    def test_get_current_user_no_token(self):
        """Test getting current user without token."""
        response = client.get("/auth/me")
        
        assert response.status_code == 403  # No token provided
        
    def test_get_current_user_invalid_token(self):
        """Test getting current user with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        
    def test_logout(self):
        """Test logout endpoint."""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "password"}
        )
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "message" in response.json()
        
    def test_refresh_token(self):
        """Test token refresh endpoint."""
        # First login to get token
        login_response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "password"}
        )
        token = login_response.json()["access_token"]
        
        # Refresh token
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        
        # New token should be different from old token (they may be the same if generated at same second)
        # Just check it's a valid JWT
        assert len(data["access_token"].split('.')) == 3


class TestAuthSecurity:
    """Test authentication security features."""
    
    def test_sql_injection_attempt(self):
        """Test SQL injection protection."""
        response = client.post(
            "/auth/login",
            json={"username": "admin'; DROP TABLE users; --", "password": "password"}
        )
        
        # Should handle gracefully (return 401, not crash)
        assert response.status_code == 401
        
    def test_xss_in_username(self):
        """Test XSS protection in username."""
        response = client.post(
            "/auth/login",
            json={"username": "<script>alert('xss')</script>", "password": "password"}
        )
        
        # Should handle gracefully
        assert response.status_code == 401
        
    def test_empty_credentials(self):
        """Test empty credentials handling."""
        response = client.post(
            "/auth/login",
            json={"username": "", "password": ""}
        )
        
        assert response.status_code == 401
        
    def test_malformed_jwt_token(self):
        """Test malformed JWT token handling."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer malformed.jwt.token"}
        )
        
        assert response.status_code == 401
        
    def test_expired_jwt_token(self):
        """Test expired JWT token handling."""
        # Create an expired token
        expired_data = {"sub": "admin", "exp": datetime.utcnow() - timedelta(hours=1)}
        expired_token = jwt.encode(expired_data, SECRET_KEY, algorithm=ALGORITHM)
        
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401


def run_tests():
    """Simple test runner without pytest."""
    print("Running Authentication Tests...")
    
    # Test classes
    test_classes = [TestBasicAuth(), TestAuthEndpoints(), TestAuthSecurity()]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n=== {test_class.__class__.__name__} ===")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            try:
                print(f"Running {test_method}...", end=" ")
                getattr(test_class, test_method)()
                print("PASSED")
                passed_tests += 1
            except Exception as e:
                print(f"FAILED: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Total: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
