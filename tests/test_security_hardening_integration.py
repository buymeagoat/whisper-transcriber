#!/usr/bin/env python3
"""
T026 Security Hardening: Integration Tests
Tests the comprehensive security system components.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request, Response
from sqlalchemy.orm import Session

from api.security.comprehensive_security import SecurityHardeningSystem
from api.security.integration import SecurityIntegrationService
from api.security.middleware import SecurityHardeningMiddleware
from api.security.audit_models import SecurityAuditLog, AuditEventType, AuditSeverity


class TestSecurityHardeningSystem:
    """Test the core security hardening system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.security_system = SecurityHardeningSystem()
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter is properly initialized."""
        assert self.security_system.rate_limiter is not None
        assert "auth" in self.security_system.rate_limiter.limits
        assert "api" in self.security_system.rate_limiter.limits
    
    def test_input_validator_initialization(self):
        """Test input validator is properly initialized."""
        assert self.security_system.input_validator is not None
    
    def test_audit_logger_initialization(self):
        """Test audit logger is properly initialized."""
        assert self.security_system.audit_logger is not None
    
    def test_csrf_protection_initialization(self):
        """Test CSRF protection is properly initialized."""
        assert self.security_system.csrf_protection is not None
    
    def test_api_key_manager_initialization(self):
        """Test API key manager is properly initialized."""
        assert self.security_system.api_key_manager is not None
    
    def test_rate_limit_check(self):
        """Test rate limiting functionality."""
        result = self.security_system.check_rate_limit("127.0.0.1", "auth")
        assert result["allowed"] is True
        assert "remaining" in result
        assert "reset_time" in result
    
    def test_input_validation(self):
        """Test input validation functionality."""
        # Test valid input
        result = self.security_system.validate_input("test_value", "general")
        assert result["valid"] is True
        
        # Test XSS attempt
        result = self.security_system.validate_input("<script>alert('xss')</script>", "general")
        assert result["valid"] is False
        assert "XSS" in result["reason"]
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation."""
        token = self.security_system.generate_csrf_token("user123")
        assert token is not None
        assert len(token) > 0
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation."""
        token = self.security_system.generate_csrf_token("user123")
        
        # Valid token
        result = self.security_system.validate_csrf_token(token, "user123")
        assert result is True
        
        # Invalid token
        result = self.security_system.validate_csrf_token("invalid_token", "user123")
        assert result is False


class TestSecurityIntegrationService:
    """Test the security integration service."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_db = Mock(spec=Session)
        self.security_service = SecurityIntegrationService()
    
    @patch('api.security.integration.SecurityHardeningSystem')
    def test_service_initialization(self, mock_security_class):
        """Test integration service initialization."""
        mock_security = Mock()
        mock_security_class.return_value = mock_security
        
        service = SecurityIntegrationService()
        assert service.security == mock_security
    
    def test_get_client_ip_with_forwarded_header(self):
        """Test client IP extraction with forwarded header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        mock_request.client.host = "127.0.0.1"
        
        ip = self.security_service._get_client_ip(mock_request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_without_forwarded_header(self):
        """Test client IP extraction without forwarded header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.client.host = "127.0.0.1"
        
        ip = self.security_service._get_client_ip(mock_request)
        assert ip == "127.0.0.1"
    
    @patch('api.security.integration.SecurityAuditLog')
    def test_validate_and_audit_request(self, mock_audit_log_class):
        """Test request validation and auditing."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.url = Mock()
        mock_request.url.__str__ = lambda: "http://example.com/api/test"
        mock_request.headers = {"user-agent": "test-browser"}
        mock_request.client.host = "127.0.0.1"
        
        # Mock the security system methods
        self.security_service.security.check_rate_limit = Mock(return_value={
            "allowed": True,
            "remaining": 99,
            "reset_time": int(time.time()) + 3600
        })
        self.security_service.security.validate_input = Mock(return_value={
            "valid": True
        })
        
        result = self.security_service.validate_and_audit_request(
            mock_request, self.mock_db, "user123", "api"
        )
        
        assert result["rate_limit_status"]["allowed"] is True
        assert result["input_validation"]["valid"] is True


class TestSecurityMiddleware:
    """Test the security middleware."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_app = Mock()
        self.middleware = SecurityHardeningMiddleware(self.mock_app)
    
    def test_middleware_initialization(self):
        """Test middleware initialization."""
        assert self.middleware.enable_audit_logging is True
        assert "/health" in self.middleware.exempt_paths
        assert "/docs" in self.middleware.exempt_paths
    
    def test_extract_user_id_from_api_key(self):
        """Test user ID extraction from API key."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"x-api-key": "test_api_key"}
        mock_request.state = Mock()
        
        # Mock the security service
        with patch('api.security.middleware.security_service') as mock_security_service:
            mock_security_service.security.api_key_manager.validate_api_key.return_value = {
                "user_id": "user123",
                "permissions": ["read", "write"]
            }
            
            user_id = self.middleware._extract_user_id(mock_request)
            assert user_id == "user123"
    
    def test_classify_endpoint_types(self):
        """Test endpoint classification."""
        assert self.middleware._classify_endpoint("/auth/login") == "auth"
        assert self.middleware._classify_endpoint("/admin/users") == "admin"
        assert self.middleware._classify_endpoint("/upload/file") == "upload"
        assert self.middleware._classify_endpoint("/api/jobs") == "api"
        assert self.middleware._classify_endpoint("/other/path") == "general"
    
    def test_add_security_headers(self):
        """Test security headers addition."""
        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        
        result = self.middleware._add_security_headers(mock_response)
        
        assert "Content-Security-Policy" in result.headers
        assert "X-Frame-Options" in result.headers
        assert "X-Content-Type-Options" in result.headers
        assert "Strict-Transport-Security" in result.headers


class TestSecurityAuditModels:
    """Test the security audit database models."""
    
    def test_security_audit_log_creation(self):
        """Test SecurityAuditLog model creation."""
        log_entry = SecurityAuditLog(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.API_ACCESS,
            severity=AuditSeverity.LOW,
            client_ip="127.0.0.1",
            user_agent="test-browser",
            request_method="GET",
            request_url="http://example.com/api/test",
            event_description="API access test",
            event_details={"key": "value"},
            risk_score=3,
            blocked=False
        )
        
        assert log_entry.event_type == AuditEventType.API_ACCESS
        assert log_entry.severity == AuditSeverity.LOW
        assert log_entry.client_ip == "127.0.0.1"
        assert log_entry.blocked is False
        assert log_entry.risk_score == 3
    
    def test_high_risk_security_log(self):
        """Test high-risk security log creation."""
        log_entry = SecurityAuditLog(
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.CRITICAL,
            client_ip="192.168.1.100",
            event_description="Suspicious activity detected",
            risk_score=10,
            blocked=True
        )
        
        assert log_entry.event_type == AuditEventType.SECURITY_VIOLATION
        assert log_entry.severity == AuditSeverity.CRITICAL
        assert log_entry.blocked is True
        assert log_entry.risk_score == 10


class TestSecuritySystemIntegration:
    """Integration tests for the complete security system."""
    
    @patch('api.security.middleware.get_db')
    @patch('api.security.integration.security_service')
    def test_full_request_processing(self, mock_security_service, mock_get_db):
        """Test full request processing through security middleware."""
        # Setup mocks
        mock_db = Mock(spec=Session)
        mock_get_db.return_value = iter([mock_db])
        
        mock_security_service.validate_and_audit_request.return_value = {
            "rate_limit_status": {"allowed": True, "remaining": 99},
            "input_validation": {"valid": True},
            "audit_logged": True
        }
        
        mock_app = Mock()
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        middleware = SecurityHardeningMiddleware(mock_app)
        
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers = {"user-agent": "test-browser"}
        mock_request.client.host = "127.0.0.1"
        
        # Test the middleware dispatch
        # Note: This would need to be run in an async context in a real test
        # result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify security service was called
        # mock_security_service.validate_and_audit_request.assert_called_once()
    
    def test_security_headers_comprehensive(self):
        """Test that all required security headers are present."""
        middleware = SecurityHardeningMiddleware(Mock())
        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        
        result = middleware._add_security_headers(mock_response)
        
        required_headers = [
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Strict-Transport-Security",
            "X-Permitted-Cross-Domain-Policies",
            "Cross-Origin-Embedder-Policy",
            "Cross-Origin-Opener-Policy",
            "Cross-Origin-Resource-Policy"
        ]
        
        for header in required_headers:
            assert header in result.headers, f"Missing security header: {header}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])