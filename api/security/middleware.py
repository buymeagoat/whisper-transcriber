#!/usr/bin/env python3
"""
T026 Security Hardening: Security Middleware
Integrates comprehensive security features into FastAPI requests.
"""

import time
import json
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.security.integration import security_service
from api.security.comprehensive_security import SecurityHeadersMiddleware
from api.utils.logger import get_system_logger

logger = get_system_logger("security_middleware")

class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    """Main security hardening middleware for T026."""
    
    def __init__(self, app, enable_audit_logging: bool = True):
        super().__init__(app)
        self.enable_audit_logging = enable_audit_logging
        self.exempt_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico"
        }
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Skip security checks for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get database session
        db = next(get_db())
        
        try:
            # Extract user information if available
            user_id = self._extract_user_id(request)
            
            # Determine endpoint type for rate limiting
            endpoint_type = self._classify_endpoint(request.url.path)
            
            # Comprehensive security validation
            if self.enable_audit_logging:
                security_info = security_service.validate_and_audit_request(
                    request, db, user_id, endpoint_type
                )
            
            # Process the request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Log successful request completion
            if self.enable_audit_logging:
                processing_time = int((time.time() - start_time) * 1000)
                self._update_audit_log_response(db, request, response.status_code, processing_time)
            
            return response
            
        except Exception as e:
            # Log security exceptions
            if self.enable_audit_logging:
                processing_time = int((time.time() - start_time) * 1000)
                self._log_security_exception(db, request, e, processing_time)
            
            # Re-raise the exception
            raise
        
        finally:
            db.close()
    
    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request if available."""
        # Try to get from JWT token in Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # This would normally decode the JWT token
                # For now, we'll extract from request state if available
                if hasattr(request.state, "user_id"):
                    return request.state.user_id
            except Exception:
                pass
        
        # Try to get from API key
        api_key = request.headers.get("x-api-key")
        if api_key:
            key_info = security_service.security.api_key_manager.validate_api_key(api_key)
            if key_info:
                return key_info["user_id"]
        
        return None
    
    def _classify_endpoint(self, path: str) -> str:
        """Classify endpoint type for appropriate rate limiting."""
        if path.startswith("/auth") or path.startswith("/login") or path.startswith("/register"):
            return "auth"
        elif path.startswith("/admin"):
            return "admin"
        elif path.startswith("/upload"):
            return "upload"
        elif path.startswith("/api"):
            return "api"
        else:
            return "general"
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add comprehensive security headers to response."""
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (HTTP Strict Transport Security)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        return response
    
    def _update_audit_log_response(
        self,
        db: Session,
        request: Request,
        status_code: int,
        processing_time: int
    ):
        """Update the most recent audit log with response information."""
        try:
            # This is a simplified approach - in production you'd want to track the specific log entry
            from api.security.audit_models import SecurityAuditLog
            from sqlalchemy import desc
            
            # Get the most recent audit log for this IP
            client_ip = security_service._get_client_ip(request)
            latest_log = db.query(SecurityAuditLog).filter(
                SecurityAuditLog.client_ip == client_ip,
                SecurityAuditLog.request_url == str(request.url)
            ).order_by(desc(SecurityAuditLog.timestamp)).first()
            
            if latest_log and latest_log.response_status is None:
                latest_log.response_status = status_code
                latest_log.processing_time_ms = processing_time
                db.commit()
                
        except Exception as e:
            logger.warning(f"Failed to update audit log response: {e}")
    
    def _log_security_exception(
        self,
        db: Session,
        request: Request,
        exception: Exception,
        processing_time: int
    ):
        """Log security-related exceptions."""
        try:
            from api.security.audit_models import SecurityAuditLog, AuditEventType, AuditSeverity
            
            # Determine if this is a security-related exception
            security_related = any(keyword in str(exception).lower() for keyword in [
                "rate limit", "authentication", "authorization", "csrf", "xss", "injection"
            ])
            
            if security_related:
                audit_log = SecurityAuditLog(
                    timestamp=datetime.utcnow(),
                    event_type=AuditEventType.SECURITY_VIOLATION,
                    severity=AuditSeverity.HIGH,
                    client_ip=security_service._get_client_ip(request),
                    user_agent=request.headers.get("user-agent"),
                    request_method=request.method,
                    request_url=str(request.url),
                    event_description=f"Security exception: {type(exception).__name__}",
                    event_details=json.dumps({
                        "exception_type": type(exception).__name__,
                        "exception_message": str(exception)[:500],
                        "processing_time_ms": processing_time
                    }),
                    risk_score=8,
                    blocked=True,
                    response_status=getattr(exception, "status_code", 500)
                )
                
                db.add(audit_log)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to log security exception: {e}")

class SecurityAPIKeyMiddleware(BaseHTTPMiddleware):
    """API key validation middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        self.protected_paths = {"/api/", "/admin/"}
    
    async def dispatch(self, request: Request, call_next):
        # Check if this path requires API key authentication
        requires_api_key = any(request.url.path.startswith(path) for path in self.protected_paths)
        
        if requires_api_key:
            api_key = request.headers.get("x-api-key")
            if api_key:
                # Get database session
                db = next(get_db())
                try:
                    key_info = security_service.validate_api_key(api_key, db, request)
                    if key_info:
                        # Add user info to request state
                        request.state.user_id = key_info["user_id"]
                        request.state.api_permissions = key_info["permissions"]
                finally:
                    db.close()
        
        return await call_next(request)

def create_security_middleware_stack():
    """Create the complete security middleware stack for T026."""
    def add_security_middlewares(app):
        # Add security middlewares in order (last added = first executed)
        app.add_middleware(SecurityAPIKeyMiddleware)
        app.add_middleware(SecurityHardeningMiddleware, enable_audit_logging=True)
        
        logger.info("T026 Security Hardening middleware stack initialized")
        return app
    
    return add_security_middlewares