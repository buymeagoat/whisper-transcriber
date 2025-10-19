"""
API caching middleware for the Whisper Transcriber API.
"""

import time
import hashlib
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from api.utils.logger import get_system_logger

logger = get_system_logger("api_cache")

@dataclass
class CacheConfig:
    """Cache configuration."""
    enable_caching: bool = True  # Changed from 'enabled'
    default_ttl: int = 300  # 5 minutes
    max_cache_size: int = 1000  # Maximum number of cached items
    cache_headers: bool = True

class ApiCacheMiddleware(BaseHTTPMiddleware):
    """Simple in-memory API response caching middleware."""
    
    def __init__(self, app, config: Optional[CacheConfig] = None):
        super().__init__(app)
        self.config = config or CacheConfig()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate a cache key for the request."""
        # Include method, path, and query parameters
        key_parts = [
            request.method,
            str(request.url.path),
            str(request.url.query)
        ]
        
        # Include relevant headers
        relevant_headers = ["accept", "accept-encoding", "authorization"]
        for header in relevant_headers:
            if header in request.headers:
                key_parts.append(f"{header}:{request.headers[header]}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cacheable(self, request: Request, response: Response) -> bool:
        """Determine if the request/response should be cached."""
        if not self.config.enable_caching:
            return False
        
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        # Don't cache error responses
        if response.status_code >= 400:
            return False
        
        # Don't cache responses with cache-control: no-cache
        cache_control = response.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        # Don't cache certain paths
        skip_paths = ["/health", "/metrics", "/admin"]
        if any(skip in request.url.path for skip in skip_paths):
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next):
        """Handle caching logic."""
        cache_key = self._generate_cache_key(request)
        now = time.time()
        
        # Check cache for GET requests
        if request.method == "GET" and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            
            if now <= cache_entry["expires_at"]:
                # Cache hit
                self.access_times[cache_key] = now
                logger.debug(f"Cache hit for {request.url.path}")
                
                # Create response from cache
                response = Response(
                    content=cache_entry["content"],
                    status_code=cache_entry["status_code"],
                    headers=cache_entry["headers"]
                )
                
                if self.config.cache_headers:
                    response.headers["X-Cache"] = "HIT"
                    response.headers["X-Cache-TTL"] = str(int(cache_entry["expires_at"] - now))
                
                return response
        
        # Cache miss - process request
        response = await call_next(request)
        
        # For simple development, just return response without complex caching
        return response
