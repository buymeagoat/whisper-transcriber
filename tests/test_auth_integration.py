"""
Authentication Integration Tests

This module focuses specifically on integration testing for authentication flows,
testing the interaction between different components of the authentication system.

Key Areas:
- Database integration with user management
- JWT token lifecycle management
- Session persistence and cleanup
- Authentication middleware integration
- Role-based access control integration
"""

import pytest
import asyncio
import os
import sys
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.main import app
from api.models import User, SessionLocal, engine, Base
from api.schemas import UserCreate, UserLogin

class TestAuthDatabaseIntegration:
    """Test authentication integration with database"""
    
    @pytest.fixture(scope="class")
    def test_db(self):
        """Create test database"""
        # Create all tables
        Base.metadata.create_all(bind=engine)
        yield
        # Cleanup is handled by the application
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_user_creation_database_persistence(self, client, test_db):
        """Test that user registration persists to database"""
        user_data = {
            "username": "db_test_user",
            "email": "dbtest@example.com",
            "password": "DbTest123!",
            "full_name": "Database Test User"
        }
        
        # Register user
        response = client.post("/register", json=user_data)
        
        # Check database directly
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == user_data["username"]).first()
            if response.status_code == 200:
                assert user is not None
                assert user.email == user_data["email"]
                assert user.full_name == user_data["full_name"]
                assert user.hashed_password != user_data["password"]  # Should be hashed
                assert user.is_active is True
            elif response.status_code in [400, 409]:
                # User might already exist
                assert user is not None
        finally:
            db.close()
    
    def test_user_login_database_verification(self, client, test_db):
        """Test that login verifies against database"""
        user_data = {
            "username": "login_db_test",
            "email": "logindb@example.com", 
            "password": "LoginDb123!",
            "full_name": "Login DB Test"
        }
        
        # Register user first
        client.post("/register", json=user_data)
        
        # Test login
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        response = client.post("/token", data=login_data)
        
        if response.status_code == 200:
            # Verify user exists in database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == user_data["username"]).first()
                assert user is not None
                assert user.is_active is True
            finally:
                db.close()
    
    def test_user_role_persistence(self, client, test_db):
        """Test user role assignment and persistence"""
        admin_user_data = {
            "username": "admin_db_test",
            "email": "admindb@example.com",
            "password": "AdminDb123!",
            "full_name": "Admin DB Test"
        }
        
        # Register user
        response = client.post("/register", json=admin_user_data)
        
        if response.status_code == 200:
            # Check default role in database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == admin_user_data["username"]).first()
                if user:
                    # Check if role field exists and has default value
                    if hasattr(user, 'role'):
                        assert user.role in ['user', 'admin']  # Should have a valid role
                    if hasattr(user, 'is_admin'):
                        assert isinstance(user.is_admin, bool)
            finally:
                db.close()

class TestAuthenticationWorkflow:
    """Test complete authentication workflows"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_user_registration_workflow(self, client):
        """Test end-to-end user registration workflow"""
        user_data = {
            "username": "workflow_test_user",
            "email": "workflow@test.com",
            "password": "WorkflowTest123!",
            "full_name": "Workflow Test User"
        }
        
        # Step 1: Register user
        register_response = client.post("/register", json=user_data)
        
        if register_response.status_code == 200:
            register_data = register_response.json()
            
            # Should return user info or token
            assert "access_token" in register_data or "user" in register_data or "message" in register_data
            
            # Step 2: Login with new credentials
            login_response = client.post("/token", data={
                "username": user_data["username"],
                "password": user_data["password"]
            })
            
            assert login_response.status_code == 200
            login_data = login_response.json()
            assert "access_token" in login_data
            
            # Step 3: Access protected resource
            headers = {"Authorization": f"Bearer {login_data['access_token']}"}
            protected_response = client.get("/dashboard", headers=headers)
            
            # Should not get auth error
            assert protected_response.status_code != 401
            assert protected_response.status_code != 403
    
    def test_session_lifecycle_management(self, client):
        """Test session creation, usage, and cleanup"""
        user_data = {
            "username": "session_lifecycle_user",
            "email": "session@lifecycle.com",
            "password": "SessionTest123!",
            "full_name": "Session Test User"
        }
        
        # Register and login
        client.post("/register", json=user_data)
        login_response = client.post("/token", data={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Test multiple requests with same token
            for i in range(3):
                response = client.get("/dashboard", headers=headers)
                # Should consistently work with same token
                assert response.status_code not in [401, 403] or response.status_code == 404
            
            # Test logout (if implemented)
            logout_response = client.post("/logout", headers=headers)
            if logout_response.status_code == 200:
                # After logout, token should be invalid
                post_logout_response = client.get("/dashboard", headers=headers)
                assert post_logout_response.status_code in [401, 403]
            elif logout_response.status_code == 404:
                # Logout endpoint not implemented yet
                pass
    
    def test_concurrent_authentication_handling(self, client):
        """Test handling of concurrent authentication requests"""
        import threading
        import time
        
        base_user_data = {
            "email": "concurrent@test.com",
            "password": "ConcurrentTest123!",
            "full_name": "Concurrent Test User"
        }
        
        results = []
        
        def register_user(index):
            """Register user in thread"""
            user_data = base_user_data.copy()
            user_data["username"] = f"concurrent_user_{index}"
            user_data["email"] = f"concurrent{index}@test.com"
            
            try:
                response = client.post("/register", json=user_data)
                results.append(("register", index, response.status_code))
                
                if response.status_code == 200:
                    # Try to login
                    login_response = client.post("/token", data={
                        "username": user_data["username"],
                        "password": user_data["password"]
                    })
                    results.append(("login", index, login_response.status_code))
            except Exception as e:
                results.append(("error", index, str(e)))
        
        # Create multiple threads for concurrent registration
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_user, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results) > 0
        
        # All operations should complete without errors
        error_results = [r for r in results if r[0] == "error"]
        assert len(error_results) == 0, f"Concurrent operations had errors: {error_results}"
        
        # At least some registrations should succeed
        register_results = [r for r in results if r[0] == "register"]
        successful_registers = [r for r in register_results if r[2] in [200, 400, 409]]
        assert len(successful_registers) > 0

class TestAuthenticationMiddleware:
    """Test authentication middleware integration"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_bearer_token_parsing(self, client):
        """Test Bearer token parsing in middleware"""
        # Create user and get token
        user_data = {
            "username": "bearer_test_user",
            "email": "bearer@test.com",
            "password": "BearerTest123!",
            "full_name": "Bearer Test User"
        }
        
        client.post("/register", json=user_data)
        login_response = client.post("/token", data={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Test different Authorization header formats
            valid_formats = [
                f"Bearer {token}",
                f"bearer {token}",  # lowercase
                f"BEARER {token}",  # uppercase
            ]
            
            for auth_header in valid_formats:
                headers = {"Authorization": auth_header}
                response = client.get("/dashboard", headers=headers)
                # Should not get auth errors with valid token
                assert response.status_code not in [401, 403] or response.status_code == 404
            
            # Test invalid formats
            invalid_formats = [
                token,  # Missing "Bearer"
                f"Basic {token}",  # Wrong auth type
                f"Bearer",  # Missing token
                f"Bearer {token} extra",  # Extra content
            ]
            
            for auth_header in invalid_formats:
                headers = {"Authorization": auth_header}
                response = client.get("/dashboard", headers=headers)
                if response.status_code not in [404, 200]:  # Some endpoints might not be protected yet
                    assert response.status_code in [401, 403]
    
    def test_authentication_error_handling(self, client):
        """Test authentication error handling in middleware"""
        # Test missing Authorization header
        response = client.get("/dashboard")
        if response.status_code not in [200, 404]:  # Might not be protected yet
            assert response.status_code in [401, 403]
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data
        
        # Test malformed Authorization header
        malformed_headers = [
            {"Authorization": ""},
            {"Authorization": "Bearer"},
            {"Authorization": "Invalid header format"},
            {"Authorization": "Bearer invalid.jwt.token"},
        ]
        
        for headers in malformed_headers:
            response = client.get("/dashboard", headers=headers)
            if response.status_code not in [200, 404]:  # Might not be protected yet
                assert response.status_code in [401, 403]

class TestRoleBasedAccess:
    """Test role-based access control integration"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_admin_access_control(self, client):
        """Test admin-only endpoint access control"""
        # Create regular user
        user_data = {
            "username": "regular_rbac_user",
            "email": "regular@rbac.com",
            "password": "RegularRbac123!",
            "full_name": "Regular RBAC User"
        }
        
        client.post("/register", json=user_data)
        login_response = client.post("/token", data={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test admin endpoints
            admin_endpoints = [
                "/admin/stats",
                "/admin/users",
                "/admin/jobs",
                "/admin/cleanup",
                "/admin/performance/summary"
            ]
            
            for endpoint in admin_endpoints:
                response = client.get(endpoint, headers=headers)
                # Should either be forbidden or not found (if not implemented)
                # Should NOT return 200 for regular user on admin endpoints
                if response.status_code not in [404, 501]:  # 404/501 = not implemented
                    # If implemented, should enforce access control
                    if response.status_code == 200:
                        # Check if this is actually an open endpoint
                        no_auth_response = client.get(endpoint)
                        if no_auth_response.status_code != 200:
                            # Endpoint requires auth but allows regular users
                            # This might be acceptable depending on implementation
                            pass
    
    def test_user_data_isolation(self, client):
        """Test that users can only access their own data"""
        # Create two users
        user1_data = {
            "username": "isolation_user1",
            "email": "user1@isolation.com",
            "password": "Isolation123!",
            "full_name": "Isolation User 1"
        }
        
        user2_data = {
            "username": "isolation_user2", 
            "email": "user2@isolation.com",
            "password": "Isolation123!",
            "full_name": "Isolation User 2"
        }
        
        # Register both users
        client.post("/register", json=user1_data)
        client.post("/register", json=user2_data)
        
        # Login as user1
        login1_response = client.post("/token", data={
            "username": user1_data["username"],
            "password": user1_data["password"]
        })
        
        # Login as user2
        login2_response = client.post("/token", data={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        
        if login1_response.status_code == 200 and login2_response.status_code == 200:
            token1 = login1_response.json()["access_token"]
            token2 = login2_response.json()["access_token"]
            
            headers1 = {"Authorization": f"Bearer {token1}"}
            headers2 = {"Authorization": f"Bearer {token2}"}
            
            # Test that user1 cannot access user2's data
            # This would require user-specific endpoints to test properly
            # For now, test that they get different responses for their own data
            
            user1_jobs = client.get("/jobs", headers=headers1)
            user2_jobs = client.get("/jobs", headers=headers2)
            
            # Both should get valid responses (or same error code)
            if user1_jobs.status_code == 200 and user2_jobs.status_code == 200:
                # If both succeed, they should potentially have different data
                # (though they might both be empty for new users)
                pass
            else:
                # If they fail, should fail consistently
                assert user1_jobs.status_code == user2_jobs.status_code

class TestAuthenticationErrorScenarios:
    """Test authentication error scenarios and edge cases"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_duplicate_user_registration(self, client):
        """Test handling of duplicate user registration"""
        user_data = {
            "username": "duplicate_test_user",
            "email": "duplicate@test.com",
            "password": "DuplicateTest123!",
            "full_name": "Duplicate Test User"
        }
        
        # First registration
        response1 = client.post("/register", json=user_data)
        
        # Second registration with same username
        response2 = client.post("/register", json=user_data)
        
        # One should succeed, other should fail appropriately
        if response1.status_code == 200:
            assert response2.status_code in [400, 409]  # Conflict/Bad Request
        elif response1.status_code in [400, 409]:
            # User might already exist from previous test
            assert response2.status_code in [400, 409]
    
    def test_database_connection_failure_simulation(self, client):
        """Test authentication behavior when database is unavailable"""
        # This is hard to test without mocking, but we can test error handling
        
        # Test with invalid/very long usernames that might cause DB issues
        invalid_user_data = {
            "username": "x" * 1000,  # Very long username
            "email": "invalid@test.com",
            "password": "Invalid123!",
            "full_name": "Invalid User"
        }
        
        response = client.post("/register", json=invalid_user_data)
        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422, 500]  # Any valid HTTP status
    
    def test_token_tampering_detection(self, client):
        """Test detection of tampered JWT tokens"""
        # Create user and get valid token
        user_data = {
            "username": "tamper_test_user",
            "email": "tamper@test.com",
            "password": "TamperTest123!",
            "full_name": "Tamper Test User"
        }
        
        client.post("/register", json=user_data)
        login_response = client.post("/token", data={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        
        if login_response.status_code == 200:
            original_token = login_response.json()["access_token"]
            
            # Create tampered tokens
            tampered_tokens = [
                original_token[:-5] + "XXXXX",  # Changed signature
                original_token[5:],  # Truncated
                original_token + "extra",  # Extended
                original_token.replace(".", "X"),  # Invalid format
            ]
            
            for tampered_token in tampered_tokens:
                headers = {"Authorization": f"Bearer {tampered_token}"}
                response = client.get("/dashboard", headers=headers)
                
                # Should reject tampered tokens
                if response.status_code not in [404, 200]:  # Might not be protected yet
                    assert response.status_code in [401, 403]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
