"""
Session Security Middleware
Handles secure JWT token storage using httpOnly cookies and enhanced session management.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from api.settings import settings


class SessionSecurityMiddleware:
    """Middleware for secure session management with httpOnly cookies."""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        self.cookie_name = "auth_token"
        self.refresh_cookie_name = "refresh_token"
        
        # Secure cookie configuration
        self.cookie_config = {
            "httponly": True,
            "secure": not settings.debug,  # HTTPS only in production (when debug=False)
            "samesite": "strict" if not settings.debug else "lax",
            "max_age": 3600,  # 1 hour
            "path": "/"
        }
        
        self.refresh_cookie_config = {
            "httponly": True,
            "secure": not settings.debug,
            "samesite": "strict" if not settings.debug else "lax",
            "max_age": 604800,  # 7 days
            "path": "/auth/refresh"  # Only sent to refresh endpoint
        }
    
    def set_auth_cookies(self, response: Response, access_token: str, refresh_token: Optional[str] = None):
        """Set secure authentication cookies."""
        # Set access token cookie
        response.set_cookie(
            key=self.cookie_name,
            value=access_token,
            **self.cookie_config
        )
        
        # Set refresh token cookie if provided
        if refresh_token:
            response.set_cookie(
                key=self.refresh_cookie_name,
                value=refresh_token,
                **self.refresh_cookie_config
            )
    
    def clear_auth_cookies(self, response: Response):
        """Clear authentication cookies securely."""
        response.delete_cookie(
            key=self.cookie_name,
            path=self.cookie_config["path"],
            secure=self.cookie_config["secure"],
            samesite=self.cookie_config["samesite"]
        )
        response.delete_cookie(
            key=self.refresh_cookie_name,
            path=self.refresh_cookie_config["path"],
            secure=self.refresh_cookie_config["secure"],
            samesite=self.refresh_cookie_config["samesite"]
        )
    
    def extract_token_from_request(self, request: Request) -> Optional[str]:
        """Extract JWT token from request (cookie or header)."""
        # First try to get from cookie (preferred)
        cookie_token = request.cookies.get(self.cookie_name)
        if cookie_token:
            return cookie_token
        
        # Fall back to Authorization header for API clients
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1]
        
        return None
    
    def extract_refresh_token(self, request: Request) -> Optional[str]:
        """Extract refresh token from secure cookie."""
        return request.cookies.get(self.refresh_cookie_name)
    
    def create_secure_credentials(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Create HTTPAuthorizationCredentials from secure token storage."""
        token = self.extract_token_from_request(request)
        if token:
            return HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=token
            )
        return None
    
    def validate_session_security(self, request: Request) -> Dict[str, Any]:
        """Validate session security configuration."""
        checks = {
            "has_auth_cookie": self.cookie_name in request.cookies,
            "has_auth_header": "authorization" in request.headers,
            "user_agent_present": "user-agent" in request.headers,
            "referer_valid": self._validate_referer(request),
            "csrf_protection": self._check_csrf_protection(request)
        }
        
        return {
            "valid": all(checks.values()),
            "checks": checks,
            "security_level": self._calculate_security_level(checks)
        }
    
    def _validate_referer(self, request: Request) -> bool:
        """Validate referer header for CSRF protection."""
        referer = request.headers.get("referer")
        if not referer:
            return False
        
        # In development (debug=True), allow localhost
        if settings.debug:
            return "localhost" in referer or "127.0.0.1" in referer
        
        # In production, validate against CORS origins
        cors_origins = settings.cors_origins.split(',') if settings.cors_origins else []
        return any(origin.strip() in referer for origin in cors_origins)
    
    def _check_csrf_protection(self, request: Request) -> bool:
        """Check CSRF protection mechanisms."""
        # Check for custom header (SPA protection)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return True
        
        # Check for CSRF token in header
        csrf_token = request.headers.get("X-CSRF-Token")
        if csrf_token:
            # In a full implementation, validate the CSRF token
            return True
        
        # For cookie-based auth, require either custom header or CSRF token
        has_auth_cookie = self.cookie_name in request.cookies
        if has_auth_cookie and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            return False  # Require explicit CSRF protection
        
        return True
    
    def _calculate_security_level(self, checks: Dict[str, bool]) -> str:
        """Calculate security level based on checks."""
        passed_checks = sum(checks.values())
        total_checks = len(checks)
        
        if passed_checks == total_checks:
            return "high"
        elif passed_checks >= total_checks * 0.7:
            return "medium"
        else:
            return "low"


# Global session security instance
session_security = SessionSecurityMiddleware()


class SecureCookieAuthDependency:
    """Dependency for secure cookie-based authentication."""
    
    def __init__(self, require_auth: bool = True):
        self.require_auth = require_auth
    
    def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Extract credentials from secure cookie or header."""
        credentials = session_security.create_secure_credentials(request)
        
        if self.require_auth and not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return credentials


# Create dependency instances
secure_auth_required = SecureCookieAuthDependency(require_auth=True)
secure_auth_optional = SecureCookieAuthDependency(require_auth=False)