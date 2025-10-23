"""
Audit Middleware for automatic request/response logging
"""

import time
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.audit.security_audit_logger import (
    get_audit_logger,
    AuditEventType,
    AuditSeverity,
    AuditOutcome
)
from api.utils.logger import get_system_logger

logger = get_system_logger("audit_middleware")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit HTTP requests and responses.
    
    Features:
    - Automatic request/response logging
    - Security event detection
    - Performance monitoring
    - Selective auditing based on endpoints
    """
    
    def __init__(self, 
                 app,
                 audit_all_requests: bool = False,
                 audit_sensitive_endpoints: bool = True,
                 audit_failures: bool = True,
                 exclude_paths: Optional[list] = None):
        super().__init__(app)
        
        self.audit_all_requests = audit_all_requests
        self.audit_sensitive_endpoints = audit_sensitive_endpoints
        self.audit_failures = audit_failures
        self.exclude_paths = set(exclude_paths or ['/health', '/version', '/docs', '/openapi.json'])
        
        # Sensitive endpoints that should always be audited
        self.sensitive_endpoints = {
            '/api/auth/login',
            '/api/auth/logout',
            '/api/auth/register',
            '/api/auth/change-password',
            '/api/admin/',
            '/api/jobs/',
            '/api/users/',
            '/api/backup/',
            '/api/config/'
        }
        
        self.audit_logger = get_audit_logger()
    
    def _should_audit_request(self, request: Request) -> bool:
        """Determine if request should be audited"""
        
        path = request.url.path
        
        # Skip excluded paths
        if path in self.exclude_paths:
            return False
        
        # Always audit sensitive endpoints
        if self.audit_sensitive_endpoints:
            for sensitive_path in self.sensitive_endpoints:
                if path.startswith(sensitive_path):
                    return True
        
        # Audit all requests if configured
        if self.audit_all_requests:
            return True
        
        return False
    
    def _extract_user_context(self, request: Request) -> Dict[str, Optional[str]]:
        """Extract user context from request"""
        
        user_id = None
        session_id = None
        
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user'):
            user = getattr(request.state, 'user', None)
            if user:
                user_id = getattr(user, 'username', None) or getattr(user, 'id', None)
        
        # Try to get session from cookies or headers
        session_id = request.cookies.get('session_id') or request.headers.get('x-session-id')
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get('user-agent')
        }
    
    def _determine_event_type(self, request: Request, response: Response) -> AuditEventType:
        """Determine appropriate audit event type based on request"""
        
        path = request.url.path.lower()
        method = request.method.upper()
        
        # Authentication endpoints
        if '/auth/' in path:
            if 'login' in path:
                return AuditEventType.LOGIN_SUCCESS if response.status_code < 400 else AuditEventType.LOGIN_FAILURE
            elif 'logout' in path:
                return AuditEventType.LOGOUT
            elif 'register' in path:
                return AuditEventType.ADMIN_USER_CREATE
            elif 'password' in path:
                return AuditEventType.PASSWORD_CHANGE
        
        # Data operations
        if method == 'POST' and response.status_code < 400:
            return AuditEventType.DATA_CREATE
        elif method == 'GET':
            return AuditEventType.DATA_READ
        elif method in ['PUT', 'PATCH'] and response.status_code < 400:
            return AuditEventType.DATA_UPDATE
        elif method == 'DELETE' and response.status_code < 400:
            return AuditEventType.DATA_DELETE
        
        # Admin operations
        if '/admin/' in path:
            return AuditEventType.ADMIN_CONFIG_CHANGE
        
        # File operations
        if '/upload' in path or '/files/' in path:
            if method == 'POST':
                return AuditEventType.FILE_UPLOAD
            elif method == 'GET':
                return AuditEventType.FILE_DOWNLOAD
            elif method == 'DELETE':
                return AuditEventType.FILE_DELETE
        
        # Default to data read for GET, data create for others
        return AuditEventType.DATA_READ if method == 'GET' else AuditEventType.DATA_CREATE
    
    def _determine_severity(self, request: Request, response: Response) -> AuditSeverity:
        """Determine audit event severity"""
        
        path = request.url.path.lower()
        
        # High severity operations
        if any(keyword in path for keyword in ['/admin/', '/delete', '/backup', '/restore']):
            return AuditSeverity.HIGH
        
        # Medium severity for authentication
        if '/auth/' in path:
            return AuditSeverity.MEDIUM
        
        # High severity for failures
        if response.status_code >= 400:
            return AuditSeverity.HIGH if response.status_code >= 500 else AuditSeverity.MEDIUM
        
        return AuditSeverity.LOW
    
    def _get_additional_data(self, request: Request, response: Response, 
                           processing_time: float) -> Dict[str, Any]:
        """Get additional data for audit log"""
        
        data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "content_length": response.headers.get("content-length"),
            "referer": request.headers.get("referer")
        }
        
        # Add request body size for uploads
        if request.headers.get("content-length"):
            data["request_size"] = request.headers.get("content-length")
        
        # Add error details for failures
        if response.status_code >= 400:
            data["error_status"] = response.status_code
        
        return data
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and audit if needed"""
        
        # Check if we should audit this request
        should_audit = self._should_audit_request(request)
        
        # Record start time for performance tracking
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Audit if needed
            if should_audit or (self.audit_failures and response.status_code >= 400):
                await self._audit_request(request, response, processing_time)
            
            return response
        
        except Exception as e:
            # Create error response for auditing
            processing_time = time.time() - start_time
            
            # Create a mock response for auditing
            error_response = Response(status_code=500)
            
            # Always audit exceptions
            await self._audit_request(request, error_response, processing_time, exception=str(e))
            
            # Re-raise the exception
            raise
    
    async def _audit_request(self, request: Request, response: Response, 
                           processing_time: float, exception: Optional[str] = None):
        """Audit the request/response"""
        
        try:
            # Extract user context
            user_context = self._extract_user_context(request)
            
            # Determine event details
            event_type = self._determine_event_type(request, response)
            severity = self._determine_severity(request, response)
            outcome = AuditOutcome.FAILURE if response.status_code >= 400 or exception else AuditOutcome.SUCCESS
            
            # Create message
            if exception:
                message = f"Request exception: {request.method} {request.url.path} - {exception}"
            else:
                message = f"Request: {request.method} {request.url.path} - {response.status_code}"
            
            # Get additional data
            additional_data = self._get_additional_data(request, response, processing_time)
            if exception:
                additional_data["exception"] = exception
            
            # Log audit event
            self.audit_logger.log_audit_event(
                event_type=event_type,
                message=message,
                severity=severity,
                outcome=outcome,
                user_id=user_context["user_id"],
                session_id=user_context["session_id"],
                ip_address=user_context["ip_address"],
                user_agent=user_context["user_agent"],
                resource=request.url.path,
                additional_data=additional_data
            )
        
        except Exception as audit_error:
            # Never let audit failures break the application
            logger.error(f"Failed to audit request: {audit_error}")
