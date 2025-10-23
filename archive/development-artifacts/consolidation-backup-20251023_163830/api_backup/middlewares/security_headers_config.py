"""
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
