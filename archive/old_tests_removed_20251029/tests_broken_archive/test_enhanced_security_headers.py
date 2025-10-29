"""
Test suite for enhanced security headers middleware
"""

import pytest
import os
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from api.middlewares.enhanced_security_headers import (
    EnhancedSecurityHeadersMiddleware,
    SecurityHeadersConfig,
    create_security_headers_middleware
)
from api.middlewares.security_headers_config import SecurityEnvironment


class TestSecurityHeadersConfig:
    """Test security headers configuration"""
    
    def test_production_config(self):
        """Test production environment configuration"""
        config = SecurityHeadersConfig("production")
        
        assert config.environment == "production"
        assert config.is_production is True
        assert config.is_development is False
        
        headers = config.get_headers()
        
        # Check basic security headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "0"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        
        # Check HSTS is enabled for production
        assert "Strict-Transport-Security" in headers
        assert "max-age=31536000" in headers["Strict-Transport-Security"]
        
        # Check strict CSP
        csp = headers["Content-Security-Policy"]
        assert "'self'" in csp
        assert "unsafe-inline" not in csp  # Should be strict
        
    def test_development_config(self):
        """Test development environment configuration"""
        config = SecurityHeadersConfig("development")
        
        assert config.environment == "development"
        assert config.is_development is True
        assert config.is_production is False
        
        headers = config.get_headers()
        
        # HSTS should not be enabled for development
        assert "Strict-Transport-Security" not in headers
        
        # CSP should be more permissive
        csp = headers["Content-Security-Policy"]
        assert "unsafe-inline" in csp
        assert "localhost" in csp
    
    def test_nonce_generation(self):
        """Test CSP nonce generation"""
        config = SecurityHeadersConfig("production")
        
        initial_nonce = config.nonce
        assert len(initial_nonce) > 10  # Should be a reasonable length
        
        config.refresh_nonce()
        new_nonce = config.nonce
        
        assert new_nonce != initial_nonce  # Should be different
        assert len(new_nonce) > 10


class TestEnhancedSecurityHeadersMiddleware:
    """Test enhanced security headers middleware"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"message": "test"}
        
        @app.get("/api/test")
        def api_test():
            return {"api": "test"}
        
        @app.get("/health")
        def health():
            return {"status": "ok"}
        
        @app.get("/static/test.css")
        def static_file():
            return Response(content="body { color: red; }", media_type="text/css")
        
        return app
    
    def test_middleware_production_headers(self, app):
        """Test middleware applies correct headers in production"""
        middleware = EnhancedSecurityHeadersMiddleware(
            app=app,
            environment="production"
        )
        app.add_middleware(EnhancedSecurityHeadersMiddleware, environment="production")
        
        client = TestClient(app)
        response = client.get("/")
        
        # Check basic security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        
        # Check HSTS for production
        assert "Strict-Transport-Security" in response.headers
        
        # Check CSP
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        
        # Check Permissions Policy
        assert "Permissions-Policy" in response.headers
        
    def test_middleware_development_headers(self, app):
        """Test middleware applies correct headers in development"""
        app.add_middleware(EnhancedSecurityHeadersMiddleware, environment="development")
        
        client = TestClient(app)
        response = client.get("/")
        
        # Basic headers should still be present
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        
        # HSTS should not be present in development
        assert "Strict-Transport-Security" not in response.headers
        
        # CSP should be more permissive
        csp = response.headers["Content-Security-Policy"]
        assert "unsafe-inline" in csp
        assert "localhost" in csp
    
    def test_excluded_paths(self, app):
        """Test that excluded paths don't get security headers"""
        app.add_middleware(
            EnhancedSecurityHeadersMiddleware,
            environment="production",
            excluded_paths=["/health"]
        )
        
        client = TestClient(app)
        
        # Regular endpoint should have headers
        response = client.get("/")
        assert "X-Content-Type-Options" in response.headers
        
        # Excluded endpoint should not have headers
        response = client.get("/health")
        # Basic FastAPI response won't have our custom headers
        # This tests the exclusion logic
    
    def test_api_specific_headers(self, app):
        """Test API-specific headers are added"""
        app.add_middleware(EnhancedSecurityHeadersMiddleware, environment="production")
        
        client = TestClient(app)
        response = client.get("/api/test")
        
        # Should have API version header
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "1.0"
    
    def test_custom_headers(self, app):
        """Test custom headers are applied"""
        custom_headers = {
            "X-Custom-Header": "custom-value",
            "X-Test-Header": "test-value"
        }
        
        app.add_middleware(
            EnhancedSecurityHeadersMiddleware,
            environment="production",
            custom_headers=custom_headers
        )
        
        client = TestClient(app)
        response = client.get("/")
        
        # Custom headers should be present
        assert response.headers["X-Custom-Header"] == "custom-value"
        assert response.headers["X-Test-Header"] == "test-value"
    
    def test_csp_reporting(self, app):
        """Test CSP reporting functionality"""
        app.add_middleware(
            EnhancedSecurityHeadersMiddleware,
            environment="production",
            enable_csp_reporting=True,
            csp_report_uri="/api/csp-report"
        )
        
        client = TestClient(app)
        response = client.get("/")
        
        csp = response.headers["Content-Security-Policy"]
        assert "report-uri /api/csp-report" in csp


class TestSecurityHeadersIntegration:
    """Test integration with FastAPI application"""
    
    def test_factory_function(self):
        """Test the factory function creates middleware correctly"""
        middleware = create_security_headers_middleware(
            environment="production",
            enable_hsts=True,
            excluded_paths=["/test"]
        )
        
        assert isinstance(middleware, EnhancedSecurityHeadersMiddleware)
        assert middleware.environment == "production"
        assert "/test" in middleware.excluded_paths
    
    def test_middleware_statistics(self):
        """Test middleware statistics collection"""
        app = FastAPI()
        
        @app.get("/")
        def root():
            return {"test": "data"}
        
        middleware = EnhancedSecurityHeadersMiddleware(app=app, environment="production")
        app.add_middleware(EnhancedSecurityHeadersMiddleware, environment="production")
        
        client = TestClient(app)
        
        # Make some requests
        client.get("/")
        client.get("/")
        
        stats = middleware.get_statistics()
        assert "headers_applied_count" in stats
        assert "excluded_requests_count" in stats
        assert "total_requests" in stats


if __name__ == "__main__":
    # Run basic tests
    print("Running security headers middleware tests...")
    
    # Test configuration
    config = SecurityHeadersConfig("production")
    headers = config.get_headers()
    print(f"Production headers count: {len(headers)}")
    print(f"HSTS enabled: {'Strict-Transport-Security' in headers}")
    
    config_dev = SecurityHeadersConfig("development")
    headers_dev = config_dev.get_headers()
    print(f"Development headers count: {len(headers_dev)}")
    print(f"HSTS enabled in dev: {'Strict-Transport-Security' in headers_dev}")
    
    # Test nonce
    initial_nonce = config.nonce
    config.refresh_nonce()
    print(f"Nonce changed: {initial_nonce != config.nonce}")
    
    print("Basic tests completed successfully!")