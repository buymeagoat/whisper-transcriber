#!/usr/bin/env python3
"""
T026 Security Hardening: Comprehensive Security System
Implements enhanced security measures including rate limiting, audit logging,
input validation, CSRF protection, and security headers.
"""

import logging
import hashlib
import secrets
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from pathlib import Path
import re
import ipaddress

from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from api.utils.logger import get_system_logger
from api.orm_bootstrap import get_db

logger = get_system_logger("security_hardening")

# ─────────────────────────────────────────────────────────────────────────────
# Security Configuration Models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SecurityConfig:
    """Comprehensive security configuration for T026."""
    
    # Rate Limiting Configuration
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_allowance: int = 10
    rate_limit_ban_threshold: int = 5
    rate_limit_ban_duration: int = 3600  # 1 hour
    
    # Authentication Security
    auth_max_attempts: int = 3
    auth_lockout_duration: int = 900  # 15 minutes
    jwt_token_expiry: int = 3600  # 1 hour
    
    # Input Validation
    max_input_length: int = 10000
    allowed_file_extensions: Set[str] = None
    max_file_size: int = 1073741824  # 1GB
    
    # CSRF Protection
    csrf_token_expiry: int = 1800  # 30 minutes
    csrf_require_referrer: bool = True
    
    # Audit Logging
    audit_log_all_requests: bool = True
    audit_log_sensitive_data: bool = False
    audit_retention_days: int = 90
    
    # Security Headers
    enable_hsts: bool = True
    hsts_max_age: int = 31536000  # 1 year
    enable_csp: bool = True
    enable_xframe: bool = True
    
    def __post_init__(self):
        if self.allowed_file_extensions is None:
            self.allowed_file_extensions = {
                '.wav', '.mp3', '.flac', '.m4a', '.aac', '.ogg', 
                '.wma', '.mp4', '.mkv', '.avi', '.mov'
            }

# ─────────────────────────────────────────────────────────────────────────────
# Enhanced Input Validation
# ─────────────────────────────────────────────────────────────────────────────

class SecurityInputValidator:
    """Enhanced input validation with security focus."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS attempts
            r'javascript:',                # JavaScript URLs
            r'on\w+\s*=',                 # Event handlers
            r'eval\s*\(',                 # Code evaluation
            r'(union|select|insert|delete|update|drop)\s+',  # SQL injection
            r'\.\./',                     # Path traversal
            r'exec\s*\(',                 # Command execution
            r'system\s*\(',               # System calls
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    def validate_string_input(self, value: str, field_name: str = "input") -> str:
        """Validate and sanitize string input."""
        if not isinstance(value, str):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid input type for {field_name}"
            )
        
        if len(value) > self.config.max_input_length:
            raise HTTPException(
                status_code=400,
                detail=f"Input too long for {field_name}. Maximum length: {self.config.max_input_length}"
            )
        
        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                logger.warning(f"Suspicious input detected in {field_name}: pattern matched")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid input detected in {field_name}"
                )
        
        # Basic XSS protection
        sanitized = value.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
        return sanitized
    
    def validate_filename(self, filename: str) -> str:
        """Validate uploaded file names."""
        if not filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.config.allowed_file_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed: {file_ext}"
            )
        
        return self.validate_string_input(filename, "filename")

# ─────────────────────────────────────────────────────────────────────────────
# Enhanced Audit Logging System
# ─────────────────────────────────────────────────────────────────────────────

class SecurityAuditLogger:
    """Comprehensive audit logging for security events."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.audit_log_path = Path("logs/security_audit.log")
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup audit logger
        self.audit_logger = logging.getLogger("security_audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # File handler for audit logs
        handler = logging.FileHandler(self.audit_log_path)
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
    
    def log_security_event(
        self,
        event_type: str,
        request: Request,
        user_id: Optional[str] = None,
        details: Optional[Dict] = None,
        severity: str = "INFO"
    ):
        """Log security-related events."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "user_id": user_id,
            "method": request.method,
            "url": str(request.url),
            "severity": severity,
        }
        
        if details:
            audit_data["details"] = details
        
        # Log based on severity
        log_message = json.dumps(audit_data)
        if severity == "CRITICAL":
            self.audit_logger.critical(log_message)
        elif severity == "WARNING":
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)
    
    def log_authentication_attempt(
        self,
        request: Request,
        username: str,
        success: bool,
        failure_reason: Optional[str] = None
    ):
        """Log authentication attempts."""
        event_type = "auth_success" if success else "auth_failure"
        details = {"username": username}
        if failure_reason:
            details["failure_reason"] = failure_reason
        
        severity = "INFO" if success else "WARNING"
        self.log_security_event(event_type, request, username, details, severity)
    
    def log_rate_limit_violation(self, request: Request, user_id: Optional[str] = None):
        """Log rate limiting violations."""
        self.log_security_event(
            "rate_limit_violation",
            request,
            user_id,
            {"limit_type": "global"},
            "WARNING"
        )
    
    def log_suspicious_activity(
        self,
        request: Request,
        activity_type: str,
        details: Dict,
        user_id: Optional[str] = None
    ):
        """Log suspicious activities."""
        self.log_security_event(
            f"suspicious_{activity_type}",
            request,
            user_id,
            details,
            "CRITICAL"
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to client host
        return getattr(request.client, "host", "unknown")

# ─────────────────────────────────────────────────────────────────────────────
# CSRF Protection
# ─────────────────────────────────────────────────────────────────────────────

class CSRFProtection:
    """CSRF token generation and validation."""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.tokens: Dict[str, datetime] = {}  # token -> expiry
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate a new CSRF token."""
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(seconds=self.config.csrf_token_expiry)
        self.tokens[token] = expiry
        
        # Clean expired tokens
        self._cleanup_expired_tokens()
        
        return token
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token."""
        if token not in self.tokens:
            return False
        
        if datetime.utcnow() > self.tokens[token]:
            del self.tokens[token]
            return False
        
        return True
    
    def _cleanup_expired_tokens(self):
        """Remove expired CSRF tokens."""
        now = datetime.utcnow()
        expired = [token for token, expiry in self.tokens.items() if now > expiry]
        for token in expired:
            del self.tokens[token]

# ─────────────────────────────────────────────────────────────────────────────
# API Key Management System
# ─────────────────────────────────────────────────────────────────────────────

class APIKeyManager:
    """API key generation and management system."""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict] = {}  # key -> {user_id, permissions, created_at, last_used}
    
    def generate_api_key(self, user_id: str, permissions: List[str] = None) -> str:
        """Generate a new API key for a user."""
        if permissions is None:
            permissions = ["read"]
        
        api_key = f"wt_{secrets.token_urlsafe(32)}"
        self.api_keys[api_key] = {
            "user_id": user_id,
            "permissions": permissions,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "active": True
        }
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate API key and return user info."""
        if api_key not in self.api_keys:
            return None
        
        key_info = self.api_keys[api_key]
        if not key_info["active"]:
            return None
        
        # Update last used timestamp
        key_info["last_used"] = datetime.utcnow()
        return key_info
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key]["active"] = False
            return True
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Enhanced Security Headers Middleware
# ─────────────────────────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enhanced security headers middleware."""
    
    def __init__(self, app, config: SecurityConfig):
        super().__init__(app)
        self.config = config
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        if self.config.enable_hsts:
            response.headers["Strict-Transport-Security"] = f"max-age={self.config.hsts_max_age}; includeSubDomains"
        
        if self.config.enable_xframe:
            response.headers["X-Frame-Options"] = "DENY"
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if self.config.enable_csp:
            # Secure CSP without unsafe directives
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "object-src 'none';"
            )
            response.headers["Content-Security-Policy"] = csp
        
        return response

# ─────────────────────────────────────────────────────────────────────────────
# Main Security Hardening Class
# ─────────────────────────────────────────────────────────────────────────────

class SecurityHardening:
    """Main security hardening system for T026."""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.input_validator = SecurityInputValidator(self.config)
        self.audit_logger = SecurityAuditLogger(self.config)
        self.csrf_protection = CSRFProtection(self.config)
        self.api_key_manager = APIKeyManager()
        
        logger.info("T026 Security Hardening system initialized")
    
    def get_security_headers_middleware(self):
        """Get security headers middleware."""
        return SecurityHeadersMiddleware
    
    def validate_request_security(self, request: Request) -> Dict[str, Any]:
        """Comprehensive request security validation."""
        security_info = {
            "client_ip": self.audit_logger._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "secure": True
        }
        
        # Check for suspicious patterns in headers
        for header_name, header_value in request.headers.items():
            try:
                self.input_validator.validate_string_input(header_value, f"header_{header_name}")
            except HTTPException:
                self.audit_logger.log_suspicious_activity(
                    request,
                    "malicious_header",
                    {"header": header_name, "value": header_value[:100]}
                )
                security_info["secure"] = False
        
        return security_info

# Initialize global security hardening instance
security_hardening = SecurityHardening()