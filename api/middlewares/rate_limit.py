"""
Rate limiting middleware for authentication endpoints
"""
import time
import asyncio
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

# Import audit logging
from api.services.audit_logging import log_security_event, AuditEventType, AuditSeverity


class RateLimitConfig:
    """Configuration for rate limiting"""
    
    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: int = 300,  # 5 minutes
        block_duration_seconds: int = 900  # 15 minutes
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration_seconds = block_duration_seconds


class RateLimitTracker:
    """Track rate limits for IP addresses"""
    
    def __init__(self):
        # Store request timestamps for each IP
        self.request_history: Dict[str, Deque[float]] = defaultdict(deque)
        # Store blocked IPs with block expiry time
        self.blocked_ips: Dict[str, float] = {}
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, ip: str, config: RateLimitConfig) -> Tuple[bool, dict]:
        """
        Check if request from IP is allowed
        Returns (is_allowed, rate_limit_info)
        """
        async with self._lock:
            current_time = time.time()
            
            # Check if IP is currently blocked
            if ip in self.blocked_ips:
                if current_time < self.blocked_ips[ip]:
                    remaining_block = int(self.blocked_ips[ip] - current_time)
                    return False, {
                        "blocked": True,
                        "remaining_block_seconds": remaining_block,
                        "message": f"IP blocked for {remaining_block} more seconds"
                    }
                else:
                    # Block has expired, remove from blocked list
                    del self.blocked_ips[ip]
            
            # Clean old requests outside the window
            requests = self.request_history[ip]
            window_start = current_time - config.window_seconds
            
            while requests and requests[0] < window_start:
                requests.popleft()
            
            # Check if within rate limit
            if len(requests) >= config.max_requests:
                # Rate limit exceeded, block the IP
                block_until = current_time + config.block_duration_seconds
                self.blocked_ips[ip] = block_until
                
                return False, {
                    "blocked": True,
                    "remaining_block_seconds": config.block_duration_seconds,
                    "message": f"Rate limit exceeded. IP blocked for {config.block_duration_seconds} seconds"
                }
            
            # Add current request to history
            requests.append(current_time)
            
            remaining_requests = config.max_requests - len(requests)
            window_reset_seconds = int(config.window_seconds - (current_time - requests[0])) if requests else config.window_seconds
            
            return True, {
                "blocked": False,
                "remaining_requests": remaining_requests,
                "window_reset_seconds": window_reset_seconds,
                "requests_in_window": len(requests)
            }
    
    async def cleanup_expired_entries(self):
        """Clean up expired entries to prevent memory leaks"""
        async with self._lock:
            current_time = time.time()
            
            # Clean expired blocked IPs
            expired_blocks = [ip for ip, expiry in self.blocked_ips.items() if current_time >= expiry]
            for ip in expired_blocks:
                del self.blocked_ips[ip]
            
            # Clean old request histories (keep only recent windows)
            for ip, requests in list(self.request_history.items()):
                # Keep requests from the last 2 windows to be safe
                cutoff_time = current_time - (2 * 300)  # 2 * default window
                while requests and requests[0] < cutoff_time:
                    requests.popleft()
                
                # Remove empty histories
                if not requests:
                    del self.request_history[ip]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for authentication endpoints
    """
    
    def __init__(self, app, config: RateLimitConfig = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.tracker = RateLimitTracker()
        
        # Define which endpoints should be rate limited
        self.protected_endpoints = {
            "/token",
            "/register", 
            "/change-password"
        }
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded IP first (for reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    def _should_rate_limit(self, request: Request) -> bool:
        """Check if this endpoint should be rate limited"""
        path = request.url.path
        method = request.method.upper()
        
        # Only rate limit POST requests to auth endpoints
        if method != "POST":
            return False
        
        # Check if path matches any protected endpoint
        for endpoint in self.protected_endpoints:
            if path.endswith(endpoint):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process the request with rate limiting"""
        
        # Check if this request should be rate limited
        if not self._should_rate_limit(request):
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        is_allowed, rate_info = await self.tracker.is_allowed(client_ip, self.config)
        
        if not is_allowed:
            # Log rate limit exceeded event
            try:
                await log_security_event(
                    event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
                    request=request,
                    severity=AuditSeverity.HIGH,
                    details={
                        "client_ip": client_ip,
                        "endpoint": request.url.path,
                        "requests_in_window": rate_info.get("requests_in_window", 0),
                        "max_requests": self.config.max_requests,
                        "window_seconds": self.config.window_seconds
                    }
                )
            except Exception as e:
                # Don't let audit logging failure affect rate limiting
                print(f"Audit logging failed in rate limit middleware: {e}")
            
            # Return rate limit error
            error_detail = {
                "error": "rate_limit_exceeded",
                "message": rate_info["message"],
                "retry_after_seconds": rate_info.get("remaining_block_seconds", self.config.block_duration_seconds)
            }
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_detail,
                headers={
                    "Retry-After": str(rate_info.get("remaining_block_seconds", self.config.block_duration_seconds)),
                    "X-RateLimit-Limit": str(self.config.max_requests),
                    "X-RateLimit-Window": str(self.config.window_seconds),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(self.config.max_requests)
        response.headers["X-RateLimit-Window"] = str(self.config.window_seconds)
        response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining_requests", 0))
        response.headers["X-RateLimit-Reset"] = str(rate_info.get("window_reset_seconds", self.config.window_seconds))
        
        return response
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await self.tracker.cleanup_expired_entries()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue cleanup cycle
                print(f"Rate limit cleanup error: {e}")


# Factory function to create configured middleware
def create_rate_limit_middleware(
    max_requests: int = 5,
    window_seconds: int = 300,
    block_duration_seconds: int = 900
) -> type:
    """Create a rate limit middleware with custom configuration"""
    
    config = RateLimitConfig(
        max_requests=max_requests,
        window_seconds=window_seconds,
        block_duration_seconds=block_duration_seconds
    )
    
    class ConfiguredRateLimitMiddleware(RateLimitMiddleware):
        def __init__(self, app):
            super().__init__(app, config)
    
    return ConfiguredRateLimitMiddleware
