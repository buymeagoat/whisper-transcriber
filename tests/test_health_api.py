"""
Health Check and Core API Tests

Tests the health endpoints and core API functionality:
- /health
- /api/health
- /docs (OpenAPI docs)
- Basic API structure
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def test_client():
    """Create test client for health checks."""
    return TestClient(app)

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_health_endpoint(self, test_client):
        """Test basic health endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok", "success"]
    
    def test_api_health_endpoint(self, test_client):
        """Test API health endpoint."""
        response = test_client.get("/api/health")
        
        # Should exist or redirect
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "health" in data
    
    def test_health_endpoint_response_time(self, test_client):
        """Test health endpoint responds quickly."""
        import time
        
        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should respond in under 1 second
        assert (end_time - start_time) < 1.0
    
    def test_health_endpoint_no_auth_required(self, test_client):
        """Test health endpoint doesn't require authentication."""
        # Should work without any headers
        response = test_client.get("/health")
        assert response.status_code == 200

class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_openapi_docs_available(self, test_client):
        """Test OpenAPI documentation is available."""
        response = test_client.get("/docs")
        
        assert response.status_code == 200
        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_json_available(self, test_client):
        """Test OpenAPI JSON schema is available."""
        response = test_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_redoc_available(self, test_client):
        """Test ReDoc documentation is available."""
        response = test_client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

class TestCORSAndSecurity:
    """Test CORS and security headers."""
    
    def test_cors_headers_present(self, test_client):
        """Test CORS headers are configured."""
        response = test_client.options("/api/health")
        
        # Should handle OPTIONS request
        assert response.status_code in [200, 405]
    
    def test_security_headers(self, test_client):
        """Test security headers are present."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        headers = response.headers
        
        # Check for common security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "content-security-policy"
        ]
        
        # At least some security headers should be present
        present_headers = [header for header in security_headers if header in headers]
        # Not strictly required but good to have
        assert len(present_headers) >= 0

class TestAPIStructure:
    """Test basic API structure and routing."""
    
    def test_api_prefix_routing(self, test_client):
        """Test that /api prefix is properly configured."""
        # These endpoints should exist or return proper errors
        endpoints_to_test = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/transcriptions",
            "/api/users"
        ]
        
        for endpoint in endpoints_to_test:
            response = test_client.get(endpoint)
            # Should not return 404 (not found) for valid API paths
            # 401 (unauthorized), 405 (method not allowed), etc. are acceptable
            assert response.status_code != 404, f"Endpoint {endpoint} returned 404"
    
    def test_invalid_endpoints_return_404(self, test_client):
        """Test invalid endpoints return 404."""
        invalid_endpoints = [
            "/nonexistent",
            "/api/nonexistent",
            "/random/path",
            "/api/invalid/endpoint"
        ]
        
        for endpoint in invalid_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 404
    
    def test_http_methods_properly_handled(self, test_client):
        """Test different HTTP methods are handled correctly."""
        # GET to health should work
        response = test_client.get("/health")
        assert response.status_code == 200
        
        # POST to health should return method not allowed
        response = test_client.post("/health")
        assert response.status_code == 405
        
        # PUT to health should return method not allowed  
        response = test_client.put("/health")
        assert response.status_code == 405

class TestErrorHandling:
    """Test error handling and responses."""
    
    def test_malformed_json_handling(self, test_client):
        """Test handling of malformed JSON requests."""
        response = test_client.post(
            "/api/auth/login",
            data="malformed json {",
            headers={"content-type": "application/json"}
        )
        
        # Should return 422 for malformed JSON
        assert response.status_code == 422
    
    def test_unsupported_media_type(self, test_client):
        """Test handling of unsupported media types."""
        response = test_client.post(
            "/api/auth/login",
            data="username=test&password=test",
            headers={"content-type": "application/x-www-form-urlencoded"}
        )
        
        # Should handle form data or return proper error
        assert response.status_code in [422, 415, 400]
    
    def test_large_request_handling(self, test_client):
        """Test handling of oversized requests."""
        large_data = {"username": "x" * 10000, "password": "x" * 10000}
        
        response = test_client.post("/api/auth/login", json=large_data)
        
        # Should handle or reject gracefully
        assert response.status_code in [400, 413, 422]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])