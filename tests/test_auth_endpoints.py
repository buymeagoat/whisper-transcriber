"""
Comprehensive Authentication Endpoint Tests

Tests the actual authentication endpoints used by the frontend:
- /api/auth/login
- /api/auth/register  
- /api/auth/me
- /api/auth/logout

These tests validate the endpoints that the React frontend actually calls.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.models import Base, User
from api.orm_bootstrap import get_db
from api.services.user_service import user_service
import json

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_client():
    """Create test client with test database."""
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    # Override database dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    yield client
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user_data():
    """Test user data for registration and login."""
    return {
        "username": "testuser123",
        "password": "SecureTestPass123!"
    }

class TestAuthEndpoints:
    """Test class for authentication endpoints."""
    
    def test_register_new_user(self, test_client, test_user_data):
        """Test user registration via /api/auth/register."""
        response = test_client.post("/api/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"]
    
    def test_register_duplicate_user(self, test_client, test_user_data):
        """Test registration with existing username."""
        # First registration
        test_client.post("/api/auth/register", json=test_user_data)
        
        # Duplicate registration
        response = test_client.post("/api/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    def test_register_invalid_data(self, test_client):
        """Test registration with invalid data."""
        invalid_data = {
            "username": "",  # Empty username
            "password": "123"  # Too short
        }
        
        response = test_client.post("/api/auth/register", json=invalid_data)
        assert response.status_code == 422
    
    def test_login_valid_credentials(self, test_client, test_user_data):
        """Test login with valid credentials via /api/auth/login."""
        # Register user first
        test_client.post("/api/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"]
    
    def test_login_invalid_credentials(self, test_client, test_user_data):
        """Test login with invalid credentials."""
        # Register user first
        test_client.post("/api/auth/register", json=test_user_data)
        
        # Login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()
    
    def test_login_nonexistent_user(self, test_client):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistentuser",
            "password": "somepassword"
        }
        response = test_client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()
    
    def test_protected_endpoint_with_token(self, test_client, test_user_data):
        """Test accessing protected endpoint with valid token."""
        # Register and login
        test_client.post("/api/auth/register", json=test_user_data)
        login_response = test_client.post("/api/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access protected endpoint
        response = test_client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
    
    def test_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without token."""
        response = test_client.get("/api/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "not authenticated" in data["detail"].lower()
    
    def test_protected_endpoint_invalid_token(self, test_client):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = test_client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower() or "not authenticated" in data["detail"].lower()
    
    def test_logout_endpoint(self, test_client, test_user_data):
        """Test logout endpoint if implemented."""
        # Register and login
        test_client.post("/api/auth/register", json=test_user_data)
        login_response = test_client.post("/api/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Logout
        response = test_client.post("/api/auth/logout", headers=headers)
        
        # Should succeed or return not implemented
        assert response.status_code in [200, 204, 501]

class TestAuthEdgeCases:
    """Test edge cases and security scenarios."""
    
    def test_sql_injection_attempt(self, test_client):
        """Test SQL injection protection in login."""
        malicious_data = {
            "username": "admin'; DROP TABLE users; --",
            "password": "password"
        }
        
        response = test_client.post("/api/auth/login", json=malicious_data)
        # Should not crash and should return 401
        assert response.status_code == 401
    
    def test_rate_limiting_login_attempts(self, test_client):
        """Test rate limiting on login attempts."""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        # Make multiple failed attempts
        responses = []
        for _ in range(10):
            response = test_client.post("/api/auth/login", json=login_data)
            responses.append(response.status_code)
        
        # Should maintain 401 for wrong credentials
        # Rate limiting might return 429 if implemented
        for status in responses:
            assert status in [401, 429]
    
    def test_password_strength_validation(self, test_client):
        """Test password strength requirements."""
        weak_passwords = ["123", "password", "abc", ""]
        
        for weak_password in weak_passwords:
            user_data = {
                "username": f"user_{weak_password}",
                "password": weak_password
            }
            
            response = test_client.post("/api/auth/register", json=user_data)
            # Should reject weak passwords
            assert response.status_code in [400, 422]
    
    def test_username_validation(self, test_client):
        """Test username validation rules."""
        invalid_usernames = ["", "a", "admin ", "test@user", "user with spaces"]
        
        for invalid_username in invalid_usernames:
            user_data = {
                "username": invalid_username,
                "password": "SecurePass123!"
            }
            
            response = test_client.post("/api/auth/register", json=user_data)
            # Should reject invalid usernames
            assert response.status_code in [400, 422]

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])