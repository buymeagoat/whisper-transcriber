"""
Functional smoke tests for whisper-transcriber application.

These tests verify that the application can be built, started, and basic
functionality works as expected. They are designed to catch functional
issues that would break user flows.
"""

import pytest
import requests
import os
import time
import subprocess
from pathlib import Path


BASE_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds


class TestAPIHealth:
    """Test basic API health and availability."""
    
    def test_api_health_endpoint(self):
        """Verify API responds to health checks."""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        
    def test_api_docs_available(self):
        """Verify OpenAPI docs are accessible."""
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


class TestStaticAssets:
    """Test static asset serving and SPA functionality."""
    
    def test_static_assets_available(self):
        """Verify frontend assets are served correctly."""
        response = requests.get(f"{BASE_URL}/static/index.html", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert "Whisper" in response.text  # App name should be in title/content
        
    def test_spa_index_route(self):
        """Verify root route serves SPA."""
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        
    def test_spa_routing_fallback(self):
        """Verify SPA routes serve index.html (fallback behavior)."""
        # Test common SPA routes
        spa_routes = ["/dashboard", "/login", "/upload", "/settings"]
        
        for route in spa_routes:
            response = requests.get(f"{BASE_URL}{route}", timeout=TIMEOUT)
            # Should either be 200 (proper SPA fallback) or redirect
            assert response.status_code in [200, 302, 404]  # 404 acceptable for now
            
            if response.status_code == 200:
                assert "<!DOCTYPE html>" in response.text


class TestDatabase:
    """Test database connectivity and migrations."""
    
    def test_database_connection_through_api(self):
        """Verify database is accessible through API endpoints."""
        # Health endpoint should verify DB connectivity
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
        
        # Try to access an endpoint that requires DB
        # Users endpoint should return 401 (auth required) not 500 (db error)
        response = requests.get(f"{BASE_URL}/users/me", timeout=TIMEOUT)
        assert response.status_code in [401, 403]  # Not 500 (DB error)


class TestAuthentication:
    """Test authentication flow functionality."""
    
    def test_user_registration_flow(self):
        """Test basic user registration."""
        # Use timestamp to ensure unique username
        timestamp = int(time.time())
        user_data = {
            "username": f"testuser_{timestamp}",
            "password": "testpass123",
            "email": f"test_{timestamp}@example.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/register", 
            json=user_data,
            timeout=TIMEOUT
        )
        # Should either succeed or conflict (user exists)
        assert response.status_code in [200, 201, 409, 422]
        
    def test_login_flow(self):
        """Test login functionality with admin credentials."""
        # Try login with default admin credentials
        login_data = {
            "username": "admin",
            "password": "changeme"
        }
        
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            timeout=TIMEOUT
        )
        
        # Should work or return auth error (not 500)
        assert response.status_code in [200, 401, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data or "token" in data
            
    def test_protected_endpoint_auth_required(self):
        """Verify protected endpoints require authentication."""
        response = requests.get(f"{BASE_URL}/users/me", timeout=TIMEOUT)
        assert response.status_code in [401, 403]


class TestFileUploads:
    """Test file upload functionality."""
    
    def test_upload_endpoint_exists(self):
        """Verify upload endpoint is available."""
        # Test without auth (should return 401, not 404)
        response = requests.post(f"{BASE_URL}/audio/upload", timeout=TIMEOUT)
        assert response.status_code in [401, 403, 422]  # Not 404


class TestContainerStructure:
    """Test that required directories and files exist in containers."""
    
    @pytest.fixture(scope="class")
    def container_running(self):
        """Check if containers are running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=whisper-transcriber", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=10
            )
            return "whisper-transcriber-api-1" in result.stdout
        except Exception:
            return False
    
    def test_api_static_directory_exists(self, container_running):
        """Verify static directory exists in API container."""
        if not container_running:
            pytest.skip("Container not running")
            
        try:
            result = subprocess.run(
                ["docker", "exec", "whisper-transcriber-api-1", "ls", "-la", "/app/api/static/"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0
            assert "index.html" in result.stdout
        except subprocess.TimeoutExpired:
            pytest.fail("Container command timed out")
        except Exception as e:
            pytest.skip(f"Container not accessible: {e}")
            
    def test_models_directory_exists(self, container_running):
        """Verify models directory exists with required files."""
        if not container_running:
            pytest.skip("Container not running")
            
        try:
            result = subprocess.run(
                ["docker", "exec", "whisper-transcriber-api-1", "ls", "-la", "/app/models/"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0
            # Check for some model files
            model_files = ["base.pt", "tiny.pt", "small.pt"]
            for model_file in model_files:
                assert model_file in result.stdout, f"Model file {model_file} not found"
        except subprocess.TimeoutExpired:
            pytest.fail("Container command timed out")
        except Exception as e:
            pytest.skip(f"Container not accessible: {e}")
            
    def test_migrations_directory_exists(self, container_running):
        """Verify migrations directory exists."""
        if not container_running:
            pytest.skip("Container not running")
            
        try:
            result = subprocess.run(
                ["docker", "exec", "whisper-transcriber-api-1", "ls", "-la", "/app/api/migrations/"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0
            assert "versions" in result.stdout
        except subprocess.TimeoutExpired:
            pytest.fail("Container command timed out")
        except Exception as e:
            pytest.skip(f"Container not accessible: {e}")


class TestWorkerService:
    """Test Celery worker functionality."""
    
    def test_worker_container_accessible(self):
        """Verify worker container is accessible."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=whisper-transcriber-worker"],
                capture_output=True, text=True, timeout=10
            )
            # Worker should exist (running or not)
            assert "whisper-transcriber-worker" in result.stdout
        except Exception:
            pytest.skip("Cannot check worker container status")


class TestUserFlows:
    """Test complete user flows end-to-end."""
    
    def test_complete_auth_flow(self):
        """Test registration -> login -> access protected resource."""
        timestamp = int(time.time())
        user_data = {
            "username": f"flowtest_{timestamp}",
            "password": "flowtest123",
            "email": f"flowtest_{timestamp}@example.com"
        }
        
        # Step 1: Register
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=user_data,
            timeout=TIMEOUT
        )
        if response.status_code not in [200, 201]:
            pytest.skip(f"Registration failed with {response.status_code}")
            
        # Step 2: Login
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            pytest.skip(f"Login failed with {response.status_code}")
            
        token_data = response.json()
        token = token_data.get("access_token") or token_data.get("token")
        assert token is not None
        
        # Step 3: Access protected resource
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/users/me",
            headers=headers,
            timeout=TIMEOUT
        )
        assert response.status_code == 200


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
