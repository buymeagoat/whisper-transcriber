"""
Security Middleware for Request Validation and Attack Prevention.

This middleware provides comprehensive request security including:
- Request size limits and timeout protection
- Header validation and sanitization
- Malicious payload detection
- SQL injection prevention
- XSS attack prevention
- Path traversal protection
- Security headers enforcement
- Request logging for security events
"""

import re
import json
import time
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import unquote

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("security_middleware")


class SecurityConfig:
    """Security middleware configuration."""
    
    # Request size limits
    MAX_REQUEST_SIZE = 104857600  # 100MB default
    MAX_JSON_DEPTH = 10
    MAX_ARRAY_LENGTH = 1000
    MAX_STRING_LENGTH = 10000
    
    # Request timeout
    MAX_REQUEST_TIMEOUT = 300  # 5 minutes
    
    # Header validation
    MAX_HEADER_LENGTH = 8192
    MAX_HEADERS_COUNT = 50
    BLOCKED_HEADERS = {
        'x-forwarded-host',  # Prevent host header injection
        'x-original-host',
        'x-rewrite-url'
    }
    
    # Content validation
    ALLOWED_CONTENT_TYPES = {
        'application/json',
        'application/x-www-form-urlencoded', 
        'multipart/form-data',
        'text/plain',
        'audio/mpeg',
        'audio/wav',
        'audio/flac',
        'audio/ogg',
        'audio/mp4',
        'audio/webm'
    }
    
    # Security patterns to detect and block
    SQL_INJECTION_PATTERNS = [
        r"('|(\\x27)|(\\x2D))",  # SQL quotes
        r"(;|\s)(select|insert|update|delete|drop|create|alter|exec|execute)\s",
        r"(\s|^)(union|having|order\s+by)\s",
        r"(benchmark|sleep|waitfor)\s*\(",
        r"(information_schema|sys\.tables|pg_catalog)"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"eval\s*\(",
        r"expression\s*\("
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.[\\/]",
        r"[\\/]etc[\\/]",
        r"[\\/]proc[\\/]", 
        r"[\\/]sys[\\/]",
        r"[\\/]var[\\/]log",
        r"[\\/]root[\\/]",
        r"c:\\windows",
        r"c:\\program files"
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"(nc|netcat|wget|curl)\s",
        r"(bash|sh|cmd|powershell)\s",
        r"/bin/(sh|bash)",
        r"\\x[0-9a-f]{2}",  # Hex encoding
        r"%[0-9a-f]{2}"     # URL encoding of dangerous chars
    ]
    
    # User-Agent validation
    MIN_USER_AGENT_LENGTH = 10
    MAX_USER_AGENT_LENGTH = 1000
    BLOCKED_USER_AGENTS = {
        'sqlmap',
        'nikto', 
        'nessus',
        'burpsuite',
        'dirb',
        'gobuster',
        'hydra',
        'masscan'
    }
    
    # Security headers to add
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=()'
    }


class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_request_size(content_length: Optional[int]) -> None:
        """Validate request size to prevent DoS attacks."""
        if content_length and content_length > SecurityConfig.MAX_REQUEST_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request too large. Maximum size: {SecurityConfig.MAX_REQUEST_SIZE // 1024 // 1024}MB"
            )
    
    @staticmethod
    def validate_headers(headers: Dict[str, str]) -> None:
        """Validate request headers for security issues."""
        # Check header count
        if len(headers) > SecurityConfig.MAX_HEADERS_COUNT:
            raise HTTPException(
                status_code=400,
                detail="Too many headers"
            )
        
        # Validate each header
        for name, value in headers.items():
            name_lower = name.lower()
            
            # Check blocked headers
            if name_lower in SecurityConfig.BLOCKED_HEADERS:
                logger.warning(f"Blocked dangerous header: {name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Header not allowed: {name}"
                )
            
            # Check header length
            if len(name) + len(value) > SecurityConfig.MAX_HEADER_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail="Header too long"
                )
            
            # Validate specific headers
            if name_lower == 'user-agent':
                SecurityValidator._validate_user_agent(value)
            elif name_lower == 'content-type':
                SecurityValidator._validate_content_type(value)
            
            # Check for injection attempts in headers
            SecurityValidator._check_malicious_patterns(value, f"header {name}")
    
    @staticmethod
    def _validate_user_agent(user_agent: str) -> None:
        """Validate User-Agent header."""
        if not user_agent:
            return
        
        if len(user_agent) < SecurityConfig.MIN_USER_AGENT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail="Invalid User-Agent"
            )
        
        if len(user_agent) > SecurityConfig.MAX_USER_AGENT_LENGTH:
            raise HTTPException(
                status_code=400, 
                detail="User-Agent too long"
            )
        
        # Check for blocked user agents (security tools)
        user_agent_lower = user_agent.lower()
        for blocked in SecurityConfig.BLOCKED_USER_AGENTS:
            if blocked in user_agent_lower:
                logger.warning(f"Blocked security tool user-agent: {user_agent}")
                raise HTTPException(
                    status_code=403,
                    detail="Access denied"
                )
    
    @staticmethod
    def _validate_content_type(content_type: str) -> None:
        """Validate Content-Type header."""
        if not content_type:
            return
        
        # Extract base content type (without parameters)
        base_type = content_type.split(';')[0].strip().lower()
        
        if base_type not in SecurityConfig.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported content type: {base_type}"
            )
    
    @staticmethod
    def validate_url(url: str) -> None:
        """Validate URL for security issues."""
        # Decode URL to catch encoded attacks
        try:
            decoded_url = unquote(url)
        except Exception:
            decoded_url = url
        
        # Check for path traversal
        for pattern in SecurityConfig.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, decoded_url, re.IGNORECASE):
                logger.warning(f"Path traversal attempt detected: {url}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid URL path"
                )
        
        # Check for other malicious patterns
        SecurityValidator._check_malicious_patterns(decoded_url, "URL")
    
    @staticmethod
    def validate_json_payload(data: Any, max_depth: int = None) -> None:
        """Validate JSON payload structure and content."""
        if max_depth is None:
            max_depth = SecurityConfig.MAX_JSON_DEPTH
        
        SecurityValidator._validate_json_structure(data, 0, max_depth)
        SecurityValidator._validate_json_content(data)
    
    @staticmethod
    def _validate_json_structure(data: Any, depth: int, max_depth: int) -> None:
        """Validate JSON structure for DoS protection."""
        if depth > max_depth:
            raise HTTPException(
                status_code=400,
                detail="JSON structure too deeply nested"
            )
        
        if isinstance(data, dict):
            if len(data) > SecurityConfig.MAX_ARRAY_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail="JSON object too large"
                )
            
            for key, value in data.items():
                if isinstance(key, str) and len(key) > SecurityConfig.MAX_STRING_LENGTH:
                    raise HTTPException(
                        status_code=400,
                        detail="JSON key too long"
                    )
                SecurityValidator._validate_json_structure(value, depth + 1, max_depth)
        
        elif isinstance(data, list):
            if len(data) > SecurityConfig.MAX_ARRAY_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail="JSON array too large" 
                )
            
            for item in data:
                SecurityValidator._validate_json_structure(item, depth + 1, max_depth)
        
        elif isinstance(data, str):
            if len(data) > SecurityConfig.MAX_STRING_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail="JSON string too long"
                )
    
    @staticmethod
    def _validate_json_content(data: Any) -> None:
        """Validate JSON content for malicious patterns."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(key, str):
                    SecurityValidator._check_malicious_patterns(key, "JSON key")
                SecurityValidator._validate_json_content(value)
        
        elif isinstance(data, list):
            for item in data:
                SecurityValidator._validate_json_content(item)
        
        elif isinstance(data, str):
            SecurityValidator._check_malicious_patterns(data, "JSON string")
    
    @staticmethod
    def _check_malicious_patterns(text: str, context: str = "input") -> None:
        """Check text for malicious patterns."""
        if not isinstance(text, str):
            return
        
        text_lower = text.lower()
        
        # Check SQL injection patterns
        for pattern in SecurityConfig.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"SQL injection attempt detected in {context}: {text[:100]}")
                raise HTTPException(
                    status_code=400,
                    detail="Malicious content detected"
                )
        
        # Check XSS patterns
        for pattern in SecurityConfig.XSS_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"XSS attempt detected in {context}: {text[:100]}")
                raise HTTPException(
                    status_code=400,
                    detail="Malicious content detected"
                )
        
        # Check command injection patterns
        for pattern in SecurityConfig.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Command injection attempt detected in {context}: {text[:100]}")
                raise HTTPException(
                    status_code=400,
                    detail="Malicious content detected"
                )


class SecurityMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for comprehensive request security."""
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.validator = SecurityValidator()
        logger.info("Security middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security validation."""
        start_time = time.time()
        
        try:
            # Validate request size
            content_length = request.headers.get('content-length')
            if content_length:
                self.validator.validate_request_size(int(content_length))
            
            # Validate headers
            self.validator.validate_headers(dict(request.headers))
            
            # Validate URL
            self.validator.validate_url(str(request.url))
            
            # Validate JSON payload if present
            if self._is_json_request(request):
                await self._validate_json_payload(request)
            
            # Check request timeout
            if time.time() - start_time > SecurityConfig.MAX_REQUEST_TIMEOUT:
                return JSONResponse(
                    status_code=408,
                    content={"error": "request_timeout", "message": "Request timeout"}
                )
            
            # Process request through the application
            response = await call_next(request)
            
            # Add security headers
            self._add_security_headers(response)
            
            # Log successful request
            processing_time = time.time() - start_time
            logger.debug(
                f"Request processed: {request.method} {request.url.path} "
                f"({processing_time:.3f}s)"
            )
            
            return response
            
        except HTTPException as e:
            # Handle validation failures
            return JSONResponse(
                status_code=e.status_code,
                content={"error": "validation_error", "message": e.detail}
            )
            
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Security middleware error: {str(e)}", exc_info=True)
            
            # Return generic error to avoid information disclosure
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error", 
                    "message": "An error occurred processing your request"
                }
            )
    
    def _is_json_request(self, request: Request) -> bool:
        """Check if request contains JSON payload."""
        content_type = request.headers.get('content-type', '')
        return content_type.startswith('application/json')
    
    async def _validate_json_payload(self, request: Request) -> None:
        """Validate JSON payload in request body."""
        try:
            # Read body (this consumes the stream)
            body = await request.body()
            
            if body:
                # Parse JSON
                try:
                    json_data = json.loads(body)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid JSON format"
                    )
                
                # Validate structure and content
                self.validator.validate_json_payload(json_data)
                
                # Store parsed JSON in request state for reuse
                request.state.json_payload = json_data
                
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid character encoding"
            )
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value


class SecurityEventLogger:
    """Logger for security-related events."""
    
    def __init__(self):
        self.logger = logging.getLogger("security_events")
    
    def log_attack_attempt(
        self, 
        attack_type: str, 
        client_ip: str, 
        user_agent: str,
        payload: str,
        request_path: str
    ) -> None:
        """Log security attack attempt."""
        self.logger.warning(
            f"Security attack detected - Type: {attack_type}, "
            f"IP: {client_ip}, UA: {user_agent}, "
            f"Path: {request_path}, Payload: {payload[:200]}"
        )
    
    def log_rate_limit_exceeded(
        self, 
        client_ip: str, 
        user_id: Optional[str],
        endpoint: str,
        limit_type: str
    ) -> None:
        """Log rate limit exceeded event."""
        self.logger.warning(
            f"Rate limit exceeded - IP: {client_ip}, "
            f"User: {user_id or 'anonymous'}, "
            f"Endpoint: {endpoint}, Type: {limit_type}"
        )
    
    def log_authentication_failure(
        self,
        client_ip: str,
        username: str,
        failure_reason: str
    ) -> None:
        """Log authentication failure."""
        self.logger.warning(
            f"Authentication failed - IP: {client_ip}, "
            f"Username: {username}, Reason: {failure_reason}"
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        client_ip: str, 
        details: Dict[str, Any]
    ) -> None:
        """Log suspicious activity."""
        self.logger.warning(
            f"Suspicious activity - Type: {activity_type}, "
            f"IP: {client_ip}, Details: {details}"
        )


# Utility functions for integration
def create_security_middleware(
    enable_strict_validation: bool = True,
    custom_config: Optional[Dict[str, Any]] = None
) -> type:
    """Create security middleware class with configuration."""
    config = custom_config or {}
    
    if enable_strict_validation:
        # Production-level strict validation
        config.setdefault("max_request_size", 52428800)  # 50MB for production
        config.setdefault("max_json_depth", 5)
        config.setdefault("max_array_length", 100)
    
    class ConfiguredSecurityMiddleware(SecurityMiddleware):
        def __init__(self, app):
            super().__init__(app, config)
    
    return ConfiguredSecurityMiddleware


# Global security event logger instance
security_logger = SecurityEventLogger()
