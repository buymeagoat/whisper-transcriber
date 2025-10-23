"""
Rate limiting middleware for the Whisper Transcriber API.
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from api.utils.logger import get_system_logger

logger = get_system_logger("rate_limit")

@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    max_requests: int = 100  # Production-ready limit
    window_seconds: int = 60  # 1-minute window
    block_duration_seconds: int = 300  # 5-minute blocks for production
    burst_size: int = 20  # Reasonable burst allowance
    enabled: bool = True  # Production security enabled

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, config: Optional[RateLimitConfig] = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.clients: Dict[str, Dict] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limits before processing request."""
        if not self.config.enabled:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        now = time.time()
        
        # Initialize client data if not exists
        if client_ip not in self.clients:
            self.clients[client_ip] = {
                "requests": [],
                "blocked_until": 0
            }
        
        client_data = self.clients[client_ip]
        
        # Check if client is blocked
        if now < client_data["blocked_until"]:
            remaining_block = int(client_data["blocked_until"] - now)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {remaining_block} seconds.",
                headers={"Retry-After": str(remaining_block)}
            )
        
        # Clean up old requests
        cutoff = now - self.config.window_seconds
        client_data["requests"] = [
            req_time for req_time in client_data["requests"]
            if req_time > cutoff
        ]
        
        # Check rate limit
        request_count = len(client_data["requests"])
        if request_count >= self.config.max_requests:
            # Block the client
            client_data["blocked_until"] = now + self.config.block_duration_seconds
            logger.warning(f"Rate limit exceeded for {client_ip}: {request_count}/{self.config.max_requests} requests")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {request_count}/{self.config.max_requests} requests per {self.config.window_seconds} seconds",
                headers={"Retry-After": str(self.config.block_duration_seconds)}
            )
        
        # Record this request
        client_data["requests"].append(now)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.config.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.config.max_requests - len(client_data["requests"])))
        response.headers["X-RateLimit-Window"] = str(self.config.window_seconds)
        
        return response
