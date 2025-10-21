#!/usr/bin/env python3
"""
T026 Security Hardening: Enhanced Rate Limiting System
Implements comprehensive rate limiting with advanced security features.
"""

import asyncio
import time
import json
import logging
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple, List, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import ipaddress
import hashlib
import redis
from pathlib import Path

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("enhanced_rate_limiter")

@dataclass
class SecurityRateLimit:
    """Enhanced rate limit configuration with security features."""
    requests: int  # Number of requests allowed
    window: int    # Time window in seconds
    burst: Optional[int] = None  # Burst allowance
    ban_threshold: Optional[int] = None  # Auto-ban after X violations
    ban_duration: int = 3600  # Ban duration in seconds (1 hour default)

@dataclass
class EnhancedRateLimitConfig:
    """Comprehensive security-focused rate limiting configuration."""
    
    # Global rate limits (per IP) - More restrictive for security
    global_limit: SecurityRateLimit = field(default_factory=lambda: SecurityRateLimit(60, 60, ban_threshold=10))  # 60 req/min
    
    # Per-user limits (authenticated requests)
    user_limit: SecurityRateLimit = field(default_factory=lambda: SecurityRateLimit(500, 3600))  # 500 req/hour
    
    # Enhanced endpoint limits with security focus
    endpoint_limits: Dict[str, SecurityRateLimit] = field(default_factory=lambda: {
        # Authentication endpoints (very strict)
        "/token": SecurityRateLimit(3, 60, ban_threshold=5, ban_duration=900),  # 3 login attempts per minute
        "/login": SecurityRateLimit(3, 60, ban_threshold=5, ban_duration=900),
        "/register": SecurityRateLimit(2, 3600, ban_threshold=3),  # 2 registrations per hour
        "/change-password": SecurityRateLimit(2, 300, ban_threshold=3),  # 2 password changes per 5 min
        "/reset-password": SecurityRateLimit(2, 3600, ban_threshold=3),
        
        # Admin endpoints (highly restricted)
        "/admin/*": SecurityRateLimit(30, 60, ban_threshold=10),  # 30 admin requests per minute
        "/admin/delete": SecurityRateLimit(5, 300, ban_threshold=3),  # 5 deletions per 5 min
        "/admin/cleanup": SecurityRateLimit(3, 3600, ban_threshold=2),  # 3 cleanup operations per hour
        
        # File upload endpoints (resource intensive)
        "/transcribe": SecurityRateLimit(5, 3600, ban_threshold=10),  # 5 uploads per hour
        "/upload": SecurityRateLimit(10, 3600, ban_threshold=15),
        "/chunked-upload": SecurityRateLimit(20, 3600, ban_threshold=25),
        
        # API endpoints (moderate)
        "/jobs": SecurityRateLimit(60, 60),  # 60 job queries per minute
        "/jobs/*": SecurityRateLimit(30, 60),  # 30 job operations per minute
        "/api/*": SecurityRateLimit(100, 60),  # General API limit
        
        # WebSocket endpoints
        "/ws": SecurityRateLimit(10, 60),  # 10 WebSocket connections per minute
        
        # Health and monitoring (lenient but monitored)
        "/health": SecurityRateLimit(120, 60),
        "/metrics": SecurityRateLimit(30, 60, ban_threshold=100),  # Allow monitoring but detect abuse
    })
    
    # Security settings
    enable_ip_whitelist: bool = False
    ip_whitelist: List[str] = field(default_factory=lambda: [
        "127.0.0.1", "::1",  # Localhost
        # Add your monitoring/admin IPs here
    ])
    
    enable_ip_blacklist: bool = True
    ip_blacklist: List[str] = field(default_factory=list)
    
    # Automatic threat detection
    enable_threat_detection: bool = True
    suspicious_user_agents: List[str] = field(default_factory=lambda: [
        "bot", "crawler", "spider", "scraper", "scanner", 
        "sqlmap", "nikto", "nmap", "masscan", "zap",
        "burp", "curl", "wget", "python-requests"  # Suspicious automated tools
    ])
    
    # Geolocation blocking (if enabled)
    enable_geo_blocking: bool = False
    blocked_countries: List[str] = field(default_factory=list)  # ISO country codes
    
    # Advanced security features
    enable_progressive_delays: bool = True  # Increase delay with violations
    enable_captcha_challenge: bool = False  # Require CAPTCHA after violations
    enable_security_logging: bool = True
    
    # Storage and performance
    use_redis: bool = False
    redis_url: str = "redis://localhost:6379/0"
    cleanup_interval: int = 300
    max_memory_entries: int = 50000

class ThreatDetector:
    """Detects and tracks potential security threats."""
    
    def __init__(self):
        self.suspicious_patterns = [
            # SQL injection patterns
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND)\b.*=.*)",
            # XSS patterns
            r"(<script|javascript:|onerror=|onload=)",
            # Path traversal
            r"(\.\./|\.\./.*|\.\.\\)",
            # Command injection
            r"(;|\||\&|`|\$\()"
        ]
        self.threat_scores = defaultdict(int)
    
    def analyze_request(self, request: Request) -> Tuple[int, List[str]]:
        """Analyze a request for potential threats."""
        threats = []
        score = 0
        
        # Check user agent
        user_agent = request.headers.get("user-agent", "").lower()
        if any(suspicious in user_agent for suspicious in [
            "sqlmap", "nikto", "burpsuite", "acunetix", "netsparker"
        ]):
            threats.append("suspicious_user_agent")
            score += 10
        
        # Check for suspicious parameters
        for param_name, param_value in request.query_params.items():
            if any(pattern in str(param_value).lower() for pattern in [
                "select", "union", "script", "../", "eval("
            ]):
                threats.append(f"suspicious_parameter_{param_name}")
                score += 5
        
        # Check request headers for common attack vectors
        for header_name, header_value in request.headers.items():
            if header_name.lower() in ["x-forwarded-for", "x-real-ip"]:
                if "," in header_value:  # Multiple IPs might indicate proxy chaining
                    score += 2
        
        return score, threats

class EnhancedSlidingWindowCounter:
    """Enhanced sliding window counter with security features."""
    
    def __init__(self, window_size: int, max_requests: int, ban_threshold: Optional[int] = None):
        self.window_size = window_size
        self.max_requests = max_requests
        self.ban_threshold = ban_threshold
        self.requests: deque = deque()
        self.violations = 0
        self.last_violation = 0
        self.is_banned = False
        self.ban_until = 0
        self.threat_score = 0
    
    def add_request(self, timestamp: Optional[float] = None, threat_score: int = 0) -> Tuple[bool, int, float, bool]:
        """
        Add a request and check if rate limit is exceeded.
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_time, is_banned)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Check if currently banned
        if self.is_banned and timestamp < self.ban_until:
            return False, 0, self.ban_until, True
        elif self.is_banned and timestamp >= self.ban_until:
            # Ban expired, reset
            self.is_banned = False
            self.violations = max(0, self.violations - 1)  # Reduce violations over time
        
        # Clean old requests
        self._cleanup_old_requests(timestamp)
        
        # Add threat score
        self.threat_score = max(0, self.threat_score + threat_score - 1)  # Decay over time
        
        # Check if limit exceeded
        current_count = len(self.requests)
        if current_count >= self.max_requests:
            self.violations += 1
            self.last_violation = timestamp
            
            # Check for auto-ban
            if self.ban_threshold and self.violations >= self.ban_threshold:
                self.is_banned = True
                self.ban_until = timestamp + 3600  # 1 hour ban
                logger.warning(f"IP auto-banned due to {self.violations} violations")
                return False, 0, self.ban_until, True
            
            oldest_request = self.requests[0] if self.requests else timestamp
            reset_time = oldest_request + self.window_size
            return False, 0, reset_time, False
        
        # Add new request
        self.requests.append(timestamp)
        remaining = self.max_requests - (current_count + 1)
        reset_time = timestamp + self.window_size
        
        return True, remaining, reset_time, False
    
    def _cleanup_old_requests(self, current_time: float) -> None:
        """Remove requests older than the window size."""
        cutoff_time = current_time - self.window_size
        while self.requests and self.requests[0] < cutoff_time:
            self.requests.popleft()

class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with comprehensive security features."""
    
    def __init__(self, app, config: EnhancedRateLimitConfig):
        super().__init__(app)
        self.config = config
        self.counters: Dict[str, EnhancedSlidingWindowCounter] = {}
        self.threat_detector = ThreatDetector()
        self.last_cleanup = time.time()
        
        # Initialize Redis if configured
        self.redis_client = None
        if config.use_redis:
            try:
                self.redis_client = redis.from_url(config.redis_url)
                self.redis_client.ping()
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, falling back to memory")
        
        # Security logging
        if config.enable_security_logging:
            self.security_logger = logging.getLogger("security")
            handler = logging.FileHandler("logs/security_events.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.security_logger.addHandler(handler)
            self.security_logger.setLevel(logging.INFO)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through enhanced rate limiting."""
        client_ip = self._get_client_ip(request)
        
        # Check IP whitelist/blacklist first
        if not self._check_ip_allowed(client_ip):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "IP address blocked"}
            )
        
        # Threat detection
        threat_score, threats = self.threat_detector.analyze_request(request)
        
        # Get rate limit key and limits
        rate_limit_key = self._get_rate_limit_key(request, client_ip)
        limits = self._get_applicable_limits(request)
        
        # Check rate limits
        for limit_name, limit_config in limits.items():
            key = f"{rate_limit_key}:{limit_name}"
            
            # Get or create counter
            if key not in self.counters:
                self.counters[key] = EnhancedSlidingWindowCounter(
                    limit_config.window,
                    limit_config.requests,
                    limit_config.ban_threshold
                )
            
            counter = self.counters[key]
            allowed, remaining, reset_time, is_banned = counter.add_request(
                threat_score=threat_score
            )
            
            if is_banned:
                self._log_security_event(
                    "IP_AUTO_BANNED",
                    client_ip,
                    f"Auto-banned for {counter.violations} violations"
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "IP address temporarily banned",
                        "ban_until": reset_time
                    }
                )
            
            if not allowed:
                self._log_security_event(
                    "RATE_LIMIT_EXCEEDED",
                    client_ip,
                    f"Rate limit exceeded for {limit_name}"
                )
                
                # Progressive delay
                if self.config.enable_progressive_delays:
                    delay = min(counter.violations * 0.5, 5.0)  # Max 5 second delay
                    await asyncio.sleep(delay)
                
                headers = {}
                if self.config.include_headers:
                    headers.update({
                        "X-RateLimit-Limit": str(limit_config.requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(int(reset_time))
                    })
                
                if self.config.include_retry_after:
                    headers["Retry-After"] = str(int(reset_time - time.time()))
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "limit": limit_config.requests,
                        "window": limit_config.window,
                        "retry_after": int(reset_time - time.time())
                    },
                    headers=headers
                )
        
        # Log threats if detected
        if threats:
            self._log_security_event(
                "THREAT_DETECTED",
                client_ip,
                f"Threats: {', '.join(threats)}, Score: {threat_score}"
            )
        
        # Cleanup old entries periodically
        if time.time() - self.last_cleanup > self.config.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Add security headers to response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers (be careful with these in production)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _check_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed based on whitelist/blacklist."""
        if self.config.enable_ip_blacklist and ip in self.config.ip_blacklist:
            return False
        
        if self.config.enable_ip_whitelist:
            return ip in self.config.ip_whitelist
        
        return True
    
    def _get_rate_limit_key(self, request: Request, client_ip: str) -> str:
        """Generate rate limit key for the request."""
        # Use user ID if authenticated, otherwise IP
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        return f"ip:{client_ip}"
    
    def _get_applicable_limits(self, request: Request) -> Dict[str, SecurityRateLimit]:
        """Get all applicable rate limits for the request."""
        limits = {}
        
        # Always apply global limit
        limits["global"] = self.config.global_limit
        
        # Apply user limit if authenticated
        if hasattr(request.state, "user_id"):
            limits["user"] = self.config.user_limit
        
        # Find matching endpoint limits
        path = request.url.path
        for endpoint_pattern, limit in self.config.endpoint_limits.items():
            if self._matches_endpoint(path, endpoint_pattern):
                limits[f"endpoint:{endpoint_pattern}"] = limit
        
        return limits
    
    def _matches_endpoint(self, path: str, pattern: str) -> bool:
        """Check if path matches endpoint pattern."""
        if pattern.endswith("*"):
            return path.startswith(pattern[:-1])
        return path == pattern
    
    def _log_security_event(self, event_type: str, client_ip: str, details: str):
        """Log security events."""
        if self.config.enable_security_logging:
            self.security_logger.warning(
                f"{event_type} | IP: {client_ip} | {details}"
            )
    
    def _cleanup_old_entries(self):
        """Clean up old rate limit entries."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, counter in self.counters.items():
            # Remove if no recent requests and not banned
            if (not counter.requests and 
                not counter.is_banned and 
                current_time - counter.last_violation > 3600):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.counters[key]
        
        logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit entries")

def create_enhanced_rate_limit_middleware(config: Optional[EnhancedRateLimitConfig] = None):
    """Factory function to create enhanced rate limit middleware."""
    if config is None:
        config = EnhancedRateLimitConfig()
    
    def middleware_factory(app):
        return EnhancedRateLimitMiddleware(app, config)
    
    return middleware_factory

# Export configuration for easy customization
__all__ = [
    "EnhancedRateLimitConfig",
    "SecurityRateLimit", 
    "EnhancedRateLimitMiddleware",
    "create_enhanced_rate_limit_middleware"
]