"""
XSS Protection Middleware
Provides input sanitization and XSS attack prevention for the API.
"""

import re
import html
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from fastapi import Request, Response
from fastapi.routing import APIRoute
import bleach

if TYPE_CHECKING:
    from fastapi import APIRouter


class XSSProtectionMiddleware:
    """Middleware for XSS protection and input sanitization."""
    
    def __init__(self):
        # Allowed HTML tags for content that may contain markup
        self.allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'i', 'b',
            'ul', 'ol', 'li', 'blockquote', 'code', 'pre'
        ]
        
        # Allowed attributes for tags
        self.allowed_attributes = {
            '*': ['class'],
            'a': ['href', 'title'],
            'abbr': ['title'],
            'acronym': ['title']
        }
        
        # Dangerous patterns to detect
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'onfocus\s*=',
            r'eval\s*\(',
            r'expression\s*\(',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                for pattern in self.xss_patterns]
    
    def sanitize_string(self, value: str, allow_html: bool = False) -> str:
        """Sanitize a string value to prevent XSS attacks."""
        if not isinstance(value, str):
            return value
        
        # First pass: detect dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                # Log potential XSS attempt
                self._log_xss_attempt(value, pattern.pattern)
                # Replace with safe placeholder
                value = pattern.sub('[FILTERED]', value)
        
        if allow_html:
            # Clean HTML while preserving safe tags
            return bleach.clean(
                value,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                strip=True
            )
        else:
            # Escape all HTML entities
            return html.escape(value)
    
    def sanitize_dict(self, data: Dict[str, Any], html_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Recursively sanitize dictionary data."""
        if not isinstance(data, dict):
            return data
        
        html_fields = html_fields or []
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                allow_html = key in html_fields
                sanitized[key] = self.sanitize_string(value, allow_html)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value, html_fields)
            elif isinstance(value, list):
                sanitized[key] = self.sanitize_list(value, html_fields)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def sanitize_list(self, data: List[Any], html_fields: Optional[List[str]] = None) -> List[Any]:
        """Recursively sanitize list data."""
        if not isinstance(data, list):
            return data
        
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item, False))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item, html_fields))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item, html_fields))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def validate_content_type(self, request: Request) -> bool:
        """Validate that content type is safe."""
        content_type = request.headers.get("content-type", "").lower()
        
        # Allow safe content types
        safe_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
            "text/plain"
        ]
        
        for safe_type in safe_types:
            if content_type.startswith(safe_type):
                return True
        
        return False
    
    def check_request_headers(self, request: Request) -> Dict[str, Any]:
        """Check request headers for XSS protection indicators."""
        headers = {}
        
        # Check for XSS protection headers
        xss_protection = request.headers.get("x-xss-protection")
        if xss_protection:
            headers["xss_protection"] = xss_protection
        
        # Check for content type options
        content_type_options = request.headers.get("x-content-type-options")
        if content_type_options:
            headers["content_type_options"] = content_type_options
        
        # Check for frame options
        frame_options = request.headers.get("x-frame-options")
        if frame_options:
            headers["frame_options"] = frame_options
        
        return headers
    
    def add_security_headers(self, response: Response) -> None:
        """Add XSS protection headers to response."""
        # Enable XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=(), "
            "accelerometer=(), ambient-light-sensor=()"
        )
    
    def _log_xss_attempt(self, content: str, pattern: str) -> None:
        """Log potential XSS attempt for security monitoring."""
        # In a production system, this would integrate with security logging
        # For now, we'll just record that an attempt was detected
        print(f"⚠️  XSS attempt detected: pattern '{pattern[:50]}...' in content")
    
    def scan_response_content(self, content: str) -> Dict[str, Any]:
        """Scan response content for potential XSS vulnerabilities."""
        issues = []
        
        # Check for unescaped user data patterns
        unescaped_patterns = [
            r'<[^>]*\${[^}]*}[^>]*>',  # Template injection
            r'<[^>]*{{[^}]*}}[^>]*>',  # Template injection
            r'"[^"]*\${[^}]*}[^"]*"',  # String injection
        ]
        
        for pattern in unescaped_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Potential template injection: {pattern}")
        
        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "recommendations": self._get_security_recommendations(issues)
        }
    
    def _get_security_recommendations(self, issues: List[str]) -> List[str]:
        """Get security recommendations based on detected issues."""
        recommendations = []
        
        if any("template injection" in issue for issue in issues):
            recommendations.extend([
                "Ensure all user input is properly escaped",
                "Use parameterized queries for database operations",
                "Implement Content Security Policy (CSP)",
                "Validate and sanitize all input data"
            ])
        
        return recommendations


# Global XSS protection instance
xss_protection = XSSProtectionMiddleware()


class SecureAPIRoute(APIRoute):
    """Custom API route with built-in XSS protection."""
    
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            # Add XSS protection headers
            response = await original_route_handler(request)
            
            if isinstance(response, Response):
                xss_protection.add_security_headers(response)
            
            return response
        
        return custom_route_handler


def create_secure_router(*args, **kwargs) -> "APIRouter":
    """Create a router with XSS protection enabled."""
    from fastapi import APIRouter
    
    # Set the route class to our secure version
    kwargs.setdefault("route_class", SecureAPIRoute)
    
    return APIRouter(*args, **kwargs)