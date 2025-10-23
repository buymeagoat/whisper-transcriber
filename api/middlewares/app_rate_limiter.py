"""
Rate Limiting Middleware for DoS Protection and API Abuse Prevention.

This middleware provides comprehensive rate limiting with multiple strategies:
- Per-IP rate limiting
- Per-user rate limiting  
- Per-endpoint rate limiting
- Sliding window algorithm
- Memory-based storage (Redis support ready)
- Configurable limits and timeouts
- Security event logging
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import ipaddress

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("rate_limiter")


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int  # Number of requests allowed
    window: int    # Time window in seconds
    burst: Optional[int] = None  # Burst allowance (default: requests)


@dataclass 
class RateLimitConfig:
    """Comprehensive rate limiting configuration."""
    
    # Global rate limits (per IP)
    global_limit: RateLimit = field(default_factory=lambda: RateLimit(100, 60))  # 100 req/min
    
    # Per-user limits (authenticated requests)
    user_limit: RateLimit = field(default_factory=lambda: RateLimit(1000, 3600))  # 1000 req/hour
    
    # Per-endpoint limits
    endpoint_limits: Dict[str, RateLimit] = field(default_factory=lambda: {
        # Authentication endpoints (stricter)
        "/token": RateLimit(5, 60),      # 5 login attempts per minute
        "/register": RateLimit(3, 3600), # 3 registrations per hour
        "/change-password": RateLimit(3, 300),  # 3 password changes per 5 min
        
        # File upload endpoints (resource intensive)
        "/transcribe": RateLimit(10, 3600),  # 10 uploads per hour
        
        # API endpoints (moderate)
        "/jobs": RateLimit(60, 60),     # 60 job queries per minute
        "/jobs/*": RateLimit(30, 60),   # 30 job operations per minute
        
        # Health endpoints (lenient)
        "/health": RateLimit(120, 60),   # 120 health checks per minute
        "/metrics": RateLimit(60, 60),   # 60 metrics requests per minute
    })
    
    # Security settings
    enable_ip_whitelist: bool = False
    ip_whitelist: List[str] = field(default_factory=list)
    enable_ip_blacklist: bool = True
    ip_blacklist: List[str] = field(default_factory=list)
    
    # Response settings
    include_headers: bool = True
    include_retry_after: bool = True
    
    # Storage settings
    cleanup_interval: int = 300  # Clean up old entries every 5 minutes
    max_memory_entries: int = 10000  # Maximum entries to keep in memory


class SlidingWindowCounter:
    """Sliding window rate limit counter with memory management."""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: deque = deque()
        self.last_cleanup = time.time()
    
    def add_request(self, timestamp: Optional[float] = None) -> Tuple[bool, int, float]:
        """
        Add a request and check if rate limit is exceeded.
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_time)
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(timestamp)
        
        # Check if limit exceeded
        current_count = len(self.requests)
        if current_count >= self.max_requests:
            oldest_request = self.requests[0] if self.requests else timestamp
            reset_time = oldest_request + self.window_size
            return False, 0, reset_time
        
        # Add new request
        self.requests.append(timestamp)
        remaining = self.max_requests - (current_count + 1)
        reset_time = timestamp + self.window_size
        
        return True, remaining, reset_time
    
    def _cleanup_old_requests(self, current_time: float) -> None:
        """Remove requests older than the window size."""
        cutoff_time = current_time - self.window_size
        while self.requests and self.requests[0] < cutoff_time:
            self.requests.popleft()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limit statistics."""
        current_time = time.time()
        self._cleanup_old_requests(current_time)
        
        current_count = len(self.requests)
        remaining = max(0, self.max_requests - current_count)
        
        # Calculate reset time
        if self.requests:
            oldest_request = self.requests[0]
            reset_time = oldest_request + self.window_size
        else:
            reset_time = current_time + self.window_size
        
        return {
            "current_count": current_count,
            "limit": self.max_requests,
            "remaining": remaining,
            "reset_time": reset_time,
            "window_size": self.window_size
        }


class MemoryRateLimitStore:
    """Memory-based rate limit store with automatic cleanup."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.counters: Dict[str, Dict[str, SlidingWindowCounter]] = defaultdict(dict)
        self.last_cleanup = time.time()
        self._cleanup_lock = asyncio.Lock()
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit_type: str, 
        rate_limit: RateLimit
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit_type: Type of limit (global, user, endpoint)
            rate_limit: Rate limit configuration
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        # Periodic cleanup
        await self._maybe_cleanup()
        
        # Get or create counter
        counter_key = f"{limit_type}:{identifier}"
        if counter_key not in self.counters[limit_type]:
            self.counters[limit_type][counter_key] = SlidingWindowCounter(
                rate_limit.window, 
                rate_limit.requests
            )
        
        counter = self.counters[limit_type][counter_key]
        allowed, remaining, reset_time = counter.add_request()
        
        # Get detailed stats
        stats = counter.get_stats()
        
        rate_limit_info = {
            "limit": rate_limit.requests,
            "remaining": remaining,
            "reset_time": reset_time,
            "window": rate_limit.window,
            "current": stats["current_count"],
            "identifier": identifier,
            "type": limit_type
        }
        
        # Log rate limit events
        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {limit_type} for {identifier}. "
                f"Limit: {rate_limit.requests}/{rate_limit.window}s, "
                f"Current: {stats['current_count']}"
            )
        
        return allowed, rate_limit_info
    
    async def _maybe_cleanup(self) -> None:
        """Perform cleanup if needed."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.config.cleanup_interval:
            async with self._cleanup_lock:
                if current_time - self.last_cleanup > self.config.cleanup_interval:
                    await self._cleanup_old_entries()
                    self.last_cleanup = current_time
    
    async def _cleanup_old_entries(self) -> None:
        """Clean up old rate limit entries."""
        total_entries = sum(len(counters) for counters in self.counters.values())
        
        if total_entries > self.config.max_memory_entries:
            logger.info(f"Cleaning up rate limit store. Current entries: {total_entries}")
            
            # Remove empty counters and old entries
            for limit_type in list(self.counters.keys()):
                counters = self.counters[limit_type]
                for key in list(counters.keys()):
                    counter = counters[key]
                    # Clean up the counter's old requests
                    counter._cleanup_old_requests(time.time())
                    
                    # Remove if no recent requests
                    if not counter.requests:
                        del counters[key]
                
                # Remove empty limit types
                if not counters:
                    del self.counters[limit_type]
            
            final_entries = sum(len(counters) for counters in self.counters.values())
            logger.info(f"Rate limit cleanup complete. Entries: {total_entries} → {final_entries}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for comprehensive rate limiting."""
    
    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.store = MemoryRateLimitStore(self.config)
        logger.info("Rate limiting middleware initialized")
        self._log_configuration()
    
    def _log_configuration(self) -> None:
        """Log rate limiting configuration."""
        logger.info(f"Global limit: {self.config.global_limit.requests}/{self.config.global_limit.window}s")
        logger.info(f"User limit: {self.config.user_limit.requests}/{self.config.user_limit.window}s")
        logger.info(f"Endpoint limits: {len(self.config.endpoint_limits)} configured")
        for endpoint, limit in self.config.endpoint_limits.items():
            logger.info(f"  {endpoint}: {limit.requests}/{limit.window}s")
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting."""
        try:
            # Check IP whitelist/blacklist
            client_ip = self._get_client_ip(request)
            
            if self._is_ip_blocked(client_ip):
                logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
                return self._create_rate_limit_response(
                    "IP address is blocked",
                    429,
                    {}
                )
            
            if self.config.enable_ip_whitelist and not self._is_ip_whitelisted(client_ip):
                logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
                return self._create_rate_limit_response(
                    "IP address not whitelisted", 
                    403,
                    {}
                )
            
            # Apply rate limits
            rate_limit_info = await self._check_all_limits(request, client_ip)
            
            if not rate_limit_info["allowed"]:
                return self._create_rate_limit_response(
                    f"Rate limit exceeded for {rate_limit_info['type']}", 
                    429,
                    rate_limit_info
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            if self.config.include_headers:
                self._add_rate_limit_headers(response, rate_limit_info)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}", exc_info=True)
            # Allow request to proceed if rate limiting fails
            return await call_next(request)
    
    async def _check_all_limits(self, request: Request, client_ip: str) -> Dict[str, Any]:
        """Check all applicable rate limits for a request."""
        path = request.url.path
        method = request.method
        
        # Get user identifier if authenticated
        user_id = self._get_user_id(request)
        
        # Check global IP limit
        allowed, global_info = await self.store.check_rate_limit(
            client_ip, 
            "global", 
            self.config.global_limit
        )
        
        if not allowed:
            return {"allowed": False, "type": "global", **global_info}
        
        # Check user limit (if authenticated)
        if user_id:
            allowed, user_info = await self.store.check_rate_limit(
                user_id,
                "user", 
                self.config.user_limit
            )
            
            if not allowed:
                return {"allowed": False, "type": "user", **user_info}
        
        # Check endpoint-specific limits
        endpoint_limit = self._get_endpoint_limit(path, method)
        if endpoint_limit:
            identifier = user_id or client_ip  # Use user ID if available, else IP
            allowed, endpoint_info = await self.store.check_rate_limit(
                f"{identifier}:{path}",
                "endpoint",
                endpoint_limit
            )
            
            if not allowed:
                return {"allowed": False, "type": "endpoint", **endpoint_info}
        
        # All limits passed
        return {
            "allowed": True,
            "type": "allowed",
            "global": global_info,
            "user": user_info if user_id else None,
            "endpoint": endpoint_info if endpoint_limit else None
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address with proxy support."""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (closest to client)
            ip = forwarded_for.split(",")[0].strip()
            if self._is_valid_ip(ip):
                return ip
        
        # Check real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip and self._is_valid_ip(real_ip):
            return real_ip
        
        # Fallback to client host
        client_host = getattr(request.client, "host", "unknown")
        return client_host if self._is_valid_ip(client_host) else "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from authenticated request."""
        # Try to get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "username"):
            return user.username
        
        # Try to extract from JWT token in Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # This would require JWT decoding - simplified for now
                # In production, you'd decode the JWT to get user info
                return "authenticated_user"  # Placeholder
            except Exception:
                pass
        
        return None
    
    def _get_endpoint_limit(self, path: str, method: str) -> Optional[RateLimit]:
        """Get rate limit for specific endpoint."""
        # Exact path match first
        if path in self.config.endpoint_limits:
            return self.config.endpoint_limits[path]
        
        # Pattern matching for dynamic routes
        for endpoint_pattern, limit in self.config.endpoint_limits.items():
            if self._matches_endpoint_pattern(path, endpoint_pattern):
                return limit
        
        return None
    
    def _matches_endpoint_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches endpoint pattern."""
        # Simple pattern matching - could be enhanced with regex
        if pattern.endswith("/*"):
            base_pattern = pattern[:-2]
            return path.startswith(base_pattern)
        
        return path == pattern
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is a valid IP address."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is in whitelist."""
        return ip in self.config.ip_whitelist
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blacklist."""
        return self.config.enable_ip_blacklist and ip in self.config.ip_blacklist
    
    def _create_rate_limit_response(
        self, 
        message: str, 
        status_code: int, 
        rate_info: Dict[str, Any]
    ) -> JSONResponse:
        """Create rate limit exceeded response."""
        headers = {}
        
        if self.config.include_headers and rate_info:
            if "limit" in rate_info:
                headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            if "remaining" in rate_info:
                headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            if "reset_time" in rate_info and self.config.include_retry_after:
                retry_after = int(rate_info["reset_time"] - time.time())
                headers["Retry-After"] = str(max(1, retry_after))
        
        return JSONResponse(
            status_code=status_code,
            headers=headers,
            content={
                "error": "rate_limit_exceeded" if status_code == 429 else "access_denied",
                "message": message,
                "details": {
                    "retry_after": headers.get("Retry-After"),
                    "limit_type": rate_info.get("type")
                }
            }
        )
    
    def _add_rate_limit_headers(self, response: Response, rate_info: Dict[str, Any]) -> None:
        """Add rate limit headers to successful response."""
        if not self.config.include_headers:
            return
        
        # Add headers from the most restrictive limit that was checked
        for limit_source in ["endpoint", "user", "global"]:
            if limit_source in rate_info and rate_info[limit_source]:
                info = rate_info[limit_source]
                response.headers["X-RateLimit-Limit"] = str(info["limit"])
                response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
                if "reset_time" in info:
                    response.headers["X-RateLimit-Reset"] = str(int(info["reset_time"]))
                break


# Pre-configured middleware instances
def create_strict_rate_limiter() -> RateLimitMiddleware:
    """Create a strict rate limiter for production use."""
    config = RateLimitConfig(
        global_limit=RateLimit(50, 60),      # 50 requests per minute per IP
        user_limit=RateLimit(500, 3600),     # 500 requests per hour per user
        endpoint_limits={
            "/token": RateLimit(3, 60),       # 3 login attempts per minute
            "/register": RateLimit(1, 3600),  # 1 registration per hour
            "/transcribe": RateLimit(5, 3600), # 5 uploads per hour
            "/jobs": RateLimit(30, 60),       # 30 job queries per minute
        }
    )
    return RateLimitMiddleware(None, config)


def create_development_rate_limiter() -> RateLimitMiddleware:
    """Create a lenient rate limiter for development."""
    config = RateLimitConfig(
        global_limit=RateLimit(1000, 60),    # 1000 requests per minute per IP
        user_limit=RateLimit(10000, 3600),   # 10000 requests per hour per user
        endpoint_limits={
            "/token": RateLimit(20, 60),      # 20 login attempts per minute
            "/register": RateLimit(10, 3600), # 10 registrations per hour
            "/transcribe": RateLimit(100, 3600), # 100 uploads per hour
        }
    )
    return RateLimitMiddleware(None, config)
