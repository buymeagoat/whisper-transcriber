"""
API response caching middleware for improved performance
"""
import json
import time
import hashlib
from typing import Dict, Any, Optional, Set
from asyncio import Lock
from dataclasses import dataclass
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class CacheEntry:
    """Cache entry containing response data and metadata"""
    data: Any
    headers: Dict[str, str]
    status_code: int
    created_at: float
    ttl: float
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > (self.created_at + self.ttl)


class InMemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self._lock = Lock()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get cached entry if it exists and hasn't expired"""
        async with self._lock:
            entry = self.cache.get(key)
            if entry and not entry.is_expired:
                return entry
            elif entry:  # Expired entry
                del self.cache[key]
            return None
    
    async def set(self, key: str, entry: CacheEntry):
        """Store cache entry, removing oldest if at capacity"""
        async with self._lock:
            # Remove expired entries first
            self._cleanup_expired()
            
            # If still at capacity, remove oldest entries
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            self.cache[key] = entry
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > (entry.created_at + entry.ttl)
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_oldest(self):
        """Remove 10% of oldest entries to make room"""
        if not self.cache:
            return
        
        # Sort by creation time and remove oldest 10%
        sorted_items = sorted(
            self.cache.items(),
            key=lambda x: x[1].created_at
        )
        
        num_to_remove = max(1, len(sorted_items) // 10)
        for i in range(num_to_remove):
            del self.cache[sorted_items[i][0]]
    
    async def clear(self):
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            total_entries = len(self.cache)
            current_time = time.time()
            expired_count = sum(
                1 for entry in self.cache.values()
                if current_time > (entry.created_at + entry.ttl)
            )
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "valid_entries": total_entries - expired_count,
                "max_size": self.max_size,
                "memory_usage_estimate": len(json.dumps([
                    {"data": str(entry.data), "headers": entry.headers}
                    for entry in list(self.cache.values())[:10]  # Sample for estimation
                ])) * total_entries // 10
            }


class CacheConfig:
    """Configuration for API response caching"""
    
    def __init__(
        self,
        default_ttl: int = 300,  # 5 minutes
        max_cache_size: int = 1000,
        enable_caching: bool = True
    ):
        self.default_ttl = default_ttl
        self.max_cache_size = max_cache_size
        self.enable_caching = enable_caching
        
        # Define caching rules for specific endpoints
        self.endpoint_rules = {
            # Static data with longer TTL
            "/health": {"ttl": 60, "methods": ["GET"]},
            "/metrics": {"ttl": 120, "methods": ["GET"]},
            "/admin/stats": {"ttl": 300, "methods": ["GET"]},
            "/admin/audit-stats": {"ttl": 300, "methods": ["GET"]},
            "/admin/audit-event-types": {"ttl": 3600, "methods": ["GET"]},  # 1 hour
            
            # User data with shorter TTL
            "/user/settings": {"ttl": 180, "methods": ["GET"]},
            "/jobs": {"ttl": 60, "methods": ["GET"]},
            "/logs": {"ttl": 120, "methods": ["GET"]},
            
            # Model and configuration data
            "/models": {"ttl": 1800, "methods": ["GET"]},  # 30 minutes
        }
        
        # Endpoints that should never be cached
        self.no_cache_endpoints: Set[str] = {
            "/token",
            "/register", 
            "/change-password",
            "/upload",
            "/admin/cleanup",
            "/admin/server/restart",
            "/admin/server/shutdown"
        }
        
        # Endpoints with user-specific data (include user ID in cache key)
        self.user_specific_endpoints: Set[str] = {
            "/user/settings",
            "/jobs",
            "/logs"
        }


class ApiCacheMiddleware(BaseHTTPMiddleware):
    """Middleware for caching API responses"""
    
    def __init__(self, app, config: CacheConfig = None):
        super().__init__(app)
        self.config = config or CacheConfig()
        self.cache = InMemoryCache(max_size=self.config.max_cache_size)
    
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached"""
        if not self.config.enable_caching:
            return False
        
        # Only cache GET requests by default
        if request.method != "GET":
            return False
        
        path = request.url.path
        
        # Never cache certain endpoints
        if any(path.startswith(endpoint) for endpoint in self.config.no_cache_endpoints):
            return False
        
        # Cache if explicitly configured or if it's a safe GET endpoint
        return (
            any(path.startswith(endpoint) for endpoint in self.config.endpoint_rules.keys()) or
            # Cache other GET endpoints with default settings
            (request.method == "GET" and not path.startswith("/admin/"))
        )
    
    def _get_cache_key(self, request: Request, user_id: Optional[str] = None) -> str:
        """Generate cache key for request"""
        # Base key from path and query parameters
        key_components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Add user ID for user-specific endpoints
        path = request.url.path
        if any(path.startswith(endpoint) for endpoint in self.config.user_specific_endpoints):
            if user_id:
                key_components.append(f"user:{user_id}")
        
        # Add relevant headers that might affect response
        relevant_headers = ["accept", "accept-language"]
        for header in relevant_headers:
            value = request.headers.get(header)
            if value:
                key_components.append(f"{header}:{value}")
        
        # Create hash of components
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_ttl(self, request: Request) -> int:
        """Get TTL for request based on endpoint configuration"""
        path = request.url.path
        
        # Check for specific endpoint rules
        for endpoint, rules in self.config.endpoint_rules.items():
            if path.startswith(endpoint):
                if request.method in rules.get("methods", ["GET"]):
                    return rules.get("ttl", self.config.default_ttl)
        
        # Return default TTL
        return self.config.default_ttl
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request for user-specific caching"""
        # Try to get from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # This is a simplified approach - in production you'd decode the JWT
            # For now, just use part of the token as user identifier
            token = auth_header[7:]
            if len(token) >= 20:
                return hashlib.md5(token.encode()).hexdigest()[:16]
        
        return None
    
    def _should_cache_response(self, response: Response) -> bool:
        """Determine if response should be cached based on status code and headers"""
        # Only cache successful responses
        if response.status_code not in [200, 201]:
            return False
        
        # Don't cache if response has cache-control headers preventing it
        cache_control = response.headers.get("cache-control", "").lower()
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    async def dispatch(self, request: Request, call_next):
        """Process request with caching"""
        
        # Check if request should be cached
        if not self._should_cache_request(request):
            return await call_next(request)
        
        # Generate cache key
        user_id = self._extract_user_id(request)
        cache_key = self._get_cache_key(request, user_id)
        
        # Try to get from cache
        cached_entry = await self.cache.get(cache_key)
        if cached_entry:
            # Return cached response
            response = JSONResponse(
                content=cached_entry.data,
                status_code=cached_entry.status_code,
                headers=dict(cached_entry.headers)
            )
            # Add cache hit header
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Cache-TTL"] = str(int(
                (cached_entry.created_at + cached_entry.ttl) - time.time()
            ))
            return response
        
        # Not in cache, proceed with request
        response = await call_next(request)
        
        # Check if response should be cached
        if self._should_cache_response(response):
            try:
                # For JSON responses, cache the content
                if hasattr(response, 'body'):
                    content = json.loads(response.body.decode())
                    
                    # Create cache entry
                    ttl = self._get_cache_ttl(request)
                    cache_entry = CacheEntry(
                        data=content,
                        headers={k: v for k, v in response.headers.items() 
                                if k.lower() not in ["content-length", "content-encoding"]},
                        status_code=response.status_code,
                        created_at=time.time(),
                        ttl=ttl
                    )
                    
                    # Store in cache
                    await self.cache.set(cache_key, cache_entry)
                    
                    # Add cache miss header
                    response.headers["X-Cache"] = "MISS"
                    response.headers["X-Cache-TTL"] = str(ttl)
                
            except (json.JSONDecodeError, AttributeError):
                # If we can't decode as JSON or access body, don't cache
                pass
        
        return response
    
    async def clear_cache(self):
        """Clear all cached entries"""
        await self.cache.clear()
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self.cache.stats()


# Factory function to create configured middleware
def create_cache_middleware(
    default_ttl: int = 300,
    max_cache_size: int = 1000,
    enable_caching: bool = True
) -> type:
    """Create an API cache middleware with custom configuration"""
    
    config = CacheConfig(
        default_ttl=default_ttl,
        max_cache_size=max_cache_size,
        enable_caching=enable_caching
    )
    
    class ConfiguredApiCacheMiddleware(ApiCacheMiddleware):
        def __init__(self, app):
            super().__init__(app, config)
    
    return ConfiguredApiCacheMiddleware
