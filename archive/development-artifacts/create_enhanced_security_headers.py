#!/usr/bin/env python3
"""
T026 Security Hardening - Enhanced Security Headers Middleware Implementation
"""

import os
import secrets
import hashlib
from pathlib import Path

def create_enhanced_security_headers():
    """Create comprehensive security headers middleware with advanced protections"""
    
    # Enhanced Security Headers Middleware
    security_headers_content = '''"""
Enhanced Security Headers Middleware for Whisper Transcriber API.

Provides comprehensive protection against:
- XSS attacks
- Clickjacking
- MIME type confusion
- Information leakage
- Cross-site request forgery
- Content injection attacks
"""

import os
import secrets
import hashlib
from typing import Dict, Optional, List, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from api.utils.logger import get_system_logger

logger = get_system_logger()


class SecurityHeadersConfig:
    """Configuration for security headers with environment-specific settings"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment.lower()
        self.is_development = self.environment in ["development", "dev", "local"]
        self.is_production = self.environment == "production"
        self.is_test = self.environment in ["test", "testing"]
        
        # Generate nonce for CSP
        self.nonce = secrets.token_urlsafe(16)
        
        # Configure headers based on environment
        self._configure_headers()
    
    def _configure_headers(self):
        """Configure security headers based on environment"""
        
        # Basic security headers (always enabled)
        self.headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "0",  # Modern browsers handle XSS better than this header
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Permitted-Cross-Domain-Policies": "none",
            "X-Download-Options": "noopen",
            "Cache-Control": "no-cache, no-store, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        # HSTS (only for production HTTPS)
        if self.is_production:
            self.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Content Security Policy
        self._configure_csp()
        
        # Permissions Policy (Feature Policy replacement)
        self._configure_permissions_policy()
        
        # Additional security headers
        self._configure_additional_headers()
    
    def _configure_csp(self):
        """Configure Content Security Policy based on environment"""
        
        if self.is_development:
            # More permissive CSP for development
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* ws://localhost:*",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: blob:",
                "font-src 'self' data:",
                "connect-src 'self' http://localhost:* ws://localhost:* wss://localhost:*",
                "media-src 'self' blob:",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
                f"script-src-attr 'nonce-{self.nonce}'",
                f"style-src-attr 'nonce-{self.nonce}'"
            ]
        elif self.is_test:
            # Minimal CSP for testing
            csp_directives = [
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "object-src 'none'"
            ]
        else:
            # Strict CSP for production
            csp_directives = [
                "default-src 'self'",
                f"script-src 'self' 'nonce-{self.nonce}'",
                f"style-src 'self' 'nonce-{self.nonce}'",
                "img-src 'self' data:",
                "font-src 'self'",
                "connect-src 'self'",
                "media-src 'self'",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
                "upgrade-insecure-requests"
            ]
        
        self.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    def _configure_permissions_policy(self):
        """Configure Permissions Policy (formerly Feature Policy)"""
        
        # Disable potentially dangerous browser features
        permissions = [
            "accelerometer=()",
            "ambient-light-sensor=()",
            "autoplay=()",
            "battery=()",
            "camera=()",
            "cross-origin-isolated=()",
            "display-capture=()",
            "document-domain=()",
            "encrypted-media=()",
            "execution-while-not-rendered=()",
            "execution-while-out-of-viewport=()",
            "fullscreen=()",
            "geolocation=()",
            "gyroscope=()",
            "keyboard-map=()",
            "magnetometer=()",
            "microphone=()",
            "midi=()",
            "navigation-override=()",
            "payment=()",
            "picture-in-picture=()",
            "publickey-credentials-get=()",
            "screen-wake-lock=()",
            "sync-xhr=()",
            "usb=()",
            "web-share=()",
            "xr-spatial-tracking=()"
        ]
        
        self.headers["Permissions-Policy"] = ", ".join(permissions)
    
    def _configure_additional_headers(self):
        """Configure additional security headers"""
        
        # Remove server identification
        self.headers["Server"] = "Whisper-Transcriber"
        
        # Cross-Origin policies for enhanced security
        self.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        self.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        self.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Additional protection headers
        if not self.is_development:
            self.headers["Expect-CT"] = "max-age=86400, enforce"
    
    def get_headers(self) -> Dict[str, str]:
        """Get all configured security headers"""
        return self.headers.copy()
    
    def refresh_nonce(self):
        """Generate a new nonce for CSP"""
        self.nonce = secrets.token_urlsafe(16)
        self._configure_csp()  # Reconfigure CSP with new nonce


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enhanced security headers middleware with comprehensive web attack protection.
    
    Features:
    - Environment-specific configuration
    - CSP with nonce support
    - Permissions Policy
    - HSTS for production
    - XSS protection
    - Clickjacking prevention
    - MIME type confusion prevention
    - Information leakage prevention
    """
    
    def __init__(
        self,
        app,
        environment: str = None,
        custom_headers: Optional[Dict[str, str]] = None,
        excluded_paths: Optional[List[str]] = None,
        enable_csp_reporting: bool = False,
        csp_report_uri: Optional[str] = None
    ):
        super().__init__(app)
        
        # Determine environment
        self.environment = environment or os.getenv("ENVIRONMENT", "production")
        
        # Initialize security configuration
        self.config = SecurityHeadersConfig(self.environment)
        
        # Custom headers override
        self.custom_headers = custom_headers or {}
        
        # Paths to exclude from security headers
        self.excluded_paths = set(excluded_paths or [])
        
        # CSP reporting
        self.enable_csp_reporting = enable_csp_reporting
        self.csp_report_uri = csp_report_uri
        
        # Statistics
        self.headers_applied_count = 0
        self.excluded_requests_count = 0
        
        logger.info(
            f"Enhanced Security Headers Middleware initialized for {self.environment} environment"
        )
    
    def _should_apply_headers(self, request: Request) -> bool:
        """Determine if security headers should be applied to this request"""
        
        # Check excluded paths
        request_path = request.url.path
        if request_path in self.excluded_paths:
            return False
        
        # Check for specific file types that might not need all headers
        static_extensions = {".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg"}
        if any(request_path.endswith(ext) for ext in static_extensions):
            return True  # Still apply headers for static files
        
        return True
    
    def _get_request_specific_headers(self, request: Request) -> Dict[str, str]:
        """Get headers specific to the request type"""
        
        headers = self.config.get_headers().copy()
        
        # Add custom headers
        headers.update(self.custom_headers)
        
        # Modify headers based on request type
        if request.url.path.startswith("/api/"):
            # API endpoints - add API-specific headers
            headers["X-API-Version"] = "1.0"
            
        elif request.url.path.startswith("/static/"):
            # Static files - modify cache control
            headers["Cache-Control"] = "public, max-age=31536000, immutable"
            
        elif request.url.path in ["/health", "/version"]:
            # Health/monitoring endpoints - minimal caching
            headers["Cache-Control"] = "no-cache, max-age=0"
        
        # Add CSP reporting if enabled
        if self.enable_csp_reporting and self.csp_report_uri:
            current_csp = headers.get("Content-Security-Policy", "")
            if current_csp:
                headers["Content-Security-Policy"] = f"{current_csp}; report-uri {self.csp_report_uri}"
        
        return headers
    
    def _log_security_violation(self, request: Request, violation_type: str, details: str):
        """Log security-related violations or issues"""
        
        logger.warning(
            f"Security violation detected: {violation_type} - "
            f"Path: {request.url.path} - "
            f"User-Agent: {request.headers.get('user-agent', 'Unknown')} - "
            f"Details: {details}"
        )
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply security headers to responses"""
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Check if headers should be applied
            if not self._should_apply_headers(request):
                self.excluded_requests_count += 1
                return response
            
            # Get request-specific headers
            security_headers = self._get_request_specific_headers(request)
            
            # Apply headers to response
            for header_name, header_value in security_headers.items():
                response.headers[header_name] = header_value
            
            # Add nonce to response for CSP
            if hasattr(response, "context"):
                response.context = getattr(response, "context", {})
                response.context["csp_nonce"] = self.config.nonce
            
            self.headers_applied_count += 1
            
            # Log successful header application (debug level)
            if logger.isEnabledFor(10):  # DEBUG level
                logger.debug(
                    f"Applied {len(security_headers)} security headers to {request.url.path}"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in security headers middleware: {e}")
            # Return response without headers rather than failing completely
            response = await call_next(request)
            return response
    
    def get_statistics(self) -> Dict[str, int]:
        """Get middleware statistics"""
        return {
            "headers_applied_count": self.headers_applied_count,
            "excluded_requests_count": self.excluded_requests_count,
            "total_requests": self.headers_applied_count + self.excluded_requests_count
        }
    
    def refresh_csp_nonce(self):
        """Refresh the CSP nonce (should be called periodically)"""
        self.config.refresh_nonce()
        logger.debug("CSP nonce refreshed")


# Helper function for easy integration
def create_security_headers_middleware(
    environment: str = None,
    enable_hsts: bool = None,
    custom_csp: str = None,
    excluded_paths: List[str] = None
) -> EnhancedSecurityHeadersMiddleware:
    """
    Factory function to create security headers middleware with common configurations.
    
    Args:
        environment: Environment name (production, development, test)
        enable_hsts: Override HSTS setting
        custom_csp: Custom Content Security Policy
        excluded_paths: Paths to exclude from security headers
    
    Returns:
        Configured EnhancedSecurityHeadersMiddleware instance
    """
    
    custom_headers = {}
    
    # Override HSTS if specified
    if enable_hsts is not None:
        if enable_hsts:
            custom_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        else:
            custom_headers["Strict-Transport-Security"] = ""  # Will be filtered out
    
    # Override CSP if specified
    if custom_csp:
        custom_headers["Content-Security-Policy"] = custom_csp
    
    return EnhancedSecurityHeadersMiddleware(
        app=None,  # Will be set by FastAPI
        environment=environment,
        custom_headers=custom_headers,
        excluded_paths=excluded_paths
    )
'''

    # Security Headers Configuration
    config_content = '''"""
Security Headers Configuration for different environments
"""

import os
from typing import Dict, List, Optional
from enum import Enum


class SecurityEnvironment(str, Enum):
    """Supported security environments"""
    PRODUCTION = "production"
    DEVELOPMENT = "development"  
    TEST = "test"
    LOCAL = "local"


class SecurityHeadersConfig:
    """Configuration management for security headers"""
    
    # Environment-specific settings
    ENVIRONMENT_CONFIGS = {
        SecurityEnvironment.PRODUCTION: {
            "enable_hsts": True,
            "csp_strict": True,
            "enable_reporting": True,
            "cache_control": "no-cache, no-store, must-revalidate",
            "permissions_policy_strict": True
        },
        SecurityEnvironment.DEVELOPMENT: {
            "enable_hsts": False,
            "csp_strict": False,
            "enable_reporting": False,
            "cache_control": "no-cache",
            "permissions_policy_strict": False
        },
        SecurityEnvironment.TEST: {
            "enable_hsts": False,
            "csp_strict": False,
            "enable_reporting": False,
            "cache_control": "no-cache",
            "permissions_policy_strict": False
        },
        SecurityEnvironment.LOCAL: {
            "enable_hsts": False,
            "csp_strict": False,
            "enable_reporting": False,
            "cache_control": "no-cache",
            "permissions_policy_strict": False
        }
    }
    
    # Paths that should be excluded from strict security headers
    DEFAULT_EXCLUDED_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    ]
    
    # Content types that need special CSP handling
    CONTENT_TYPE_CSP_OVERRIDES = {
        "application/json": "default-src 'none'",
        "text/plain": "default-src 'none'",
        "image/": "default-src 'none'"
    }
    
    @classmethod
    def get_config(cls, environment: str) -> Dict:
        """Get configuration for specified environment"""
        env = SecurityEnvironment(environment.lower())
        return cls.ENVIRONMENT_CONFIGS.get(env, cls.ENVIRONMENT_CONFIGS[SecurityEnvironment.PRODUCTION])
    
    @classmethod
    def get_excluded_paths(cls, additional_paths: Optional[List[str]] = None) -> List[str]:
        """Get list of paths excluded from security headers"""
        paths = cls.DEFAULT_EXCLUDED_PATHS.copy()
        if additional_paths:
            paths.extend(additional_paths)
        return paths
    
    @classmethod
    def is_development_mode(cls, environment: str) -> bool:
        """Check if running in development mode"""
        return environment.lower() in ["development", "dev", "local"]
    
    @classmethod
    def should_enable_hsts(cls, environment: str, force_enable: Optional[bool] = None) -> bool:
        """Determine if HSTS should be enabled"""
        if force_enable is not None:
            return force_enable
        
        config = cls.get_config(environment)
        return config.get("enable_hsts", False)
    
    @classmethod
    def get_csp_directives(cls, environment: str, custom_directives: Optional[Dict[str, str]] = None) -> str:
        """Get Content Security Policy directives for environment"""
        
        config = cls.get_config(environment)
        is_strict = config.get("csp_strict", True)
        
        if is_strict:
            # Production/strict CSP
            directives = {
                "default-src": "'self'",
                "script-src": "'self'",
                "style-src": "'self'",
                "img-src": "'self' data:",
                "font-src": "'self'",
                "connect-src": "'self'",
                "media-src": "'self'",
                "object-src": "'none'",
                "base-uri": "'self'",
                "form-action": "'self'",
                "frame-ancestors": "'none'",
                "upgrade-insecure-requests": ""
            }
        else:
            # Development/permissive CSP
            directives = {
                "default-src": "'self'",
                "script-src": "'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* ws://localhost:*",
                "style-src": "'self' 'unsafe-inline'",
                "img-src": "'self' data: blob:",
                "font-src": "'self' data:",
                "connect-src": "'self' http://localhost:* ws://localhost:* wss://localhost:*",
                "media-src": "'self' blob:",
                "object-src": "'none'",
                "base-uri": "'self'",
                "form-action": "'self'",
                "frame-ancestors": "'none'"
            }
        
        # Apply custom directives
        if custom_directives:
            directives.update(custom_directives)
        
        # Convert to CSP string
        csp_parts = []
        for directive, value in directives.items():
            if value:  # Skip empty values
                csp_parts.append(f"{directive} {value}")
            else:
                csp_parts.append(directive)  # Directives without values (like upgrade-insecure-requests)
        
        return "; ".join(csp_parts)
'''

    # Security headers integration script
    integration_content = '''"""
Integration script for enhanced security headers middleware
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def integrate_security_headers():
    """Integrate enhanced security headers middleware into main application"""
    
    main_py_path = project_root / "api" / "main.py"
    
    if not main_py_path.exists():
        print(f"Error: {main_py_path} not found")
        return False
    
    # Read current main.py
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Check if enhanced security headers are already imported
    if "EnhancedSecurityHeadersMiddleware" in content:
        print("Enhanced security headers middleware already integrated")
        return True
    
    # Find the import section for middlewares
    import_section = """from api.middlewares.security_headers import SecurityHeadersMiddleware"""
    
    if import_section in content:
        # Replace the existing import
        new_import = """from api.middlewares.enhanced_security_headers import (
    EnhancedSecurityHeadersMiddleware,
    create_security_headers_middleware
)"""
        content = content.replace(import_section, new_import)
    else:
        # Add new import after other middleware imports
        middleware_imports = """from api.middlewares.access_log import AccessLogMiddleware"""
        if middleware_imports in content:
            content = content.replace(
                middleware_imports,
                middleware_imports + """
from api.middlewares.enhanced_security_headers import (
    EnhancedSecurityHeadersMiddleware,
    create_security_headers_middleware
)"""
            )
    
    # Find and replace the middleware setup
    old_middleware = """app.add_middleware(SecurityHeadersMiddleware, enable_hsts=False)  # HSTS disabled for development"""
    
    if old_middleware in content:
        new_middleware = """# Enhanced Security Headers with environment-specific configuration
environment = os.getenv("ENVIRONMENT", "production")
security_headers_middleware = create_security_headers_middleware(
    environment=environment,
    enable_hsts=(environment == "production"),
    excluded_paths=["/docs", "/redoc", "/openapi.json", "/health", "/version"]
)
app.add_middleware(EnhancedSecurityHeadersMiddleware, 
                  environment=environment,
                  excluded_paths=["/docs", "/redoc", "/openapi.json"])"""
        
        content = content.replace(old_middleware, new_middleware)
    
    # Write updated main.py
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print("Enhanced security headers middleware integrated successfully")
    return True

if __name__ == "__main__":
    integrate_security_headers()
'''

    # Write the enhanced security headers middleware
    middleware_path = Path("api/middlewares/enhanced_security_headers.py")
    middleware_path.parent.mkdir(exist_ok=True)
    with open(middleware_path, 'w') as f:
        f.write(security_headers_content)
    print(f"Created enhanced security headers middleware: {middleware_path}")
    
    # Write the configuration file
    config_path = Path("api/middlewares/security_headers_config.py")
    with open(config_path, 'w') as f:
        f.write(config_content)
    print(f"Created security headers configuration: {config_path}")
    
    # Write the integration script
    integration_path = Path("temp/integrate_security_headers.py")
    integration_path.parent.mkdir(exist_ok=True)
    with open(integration_path, 'w') as f:
        f.write(integration_content)
    print(f"Created integration script: {integration_path}")

if __name__ == "__main__":
    create_enhanced_security_headers()