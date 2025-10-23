"""
Enhanced API cache middleware using Redis for T025 Phase 2: API Response Caching
Provides intelligent caching with compression, invalidation, and performance monitoring.
"""

import time
import json
from typing import Dict, Optional, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.services.redis_cache import get_cache_service, CacheConfiguration
from api.utils.logger import get_system_logger

logger = get_system_logger("enhanced_cache_middleware")

class EnhancedApiCacheMiddleware(BaseHTTPMiddleware):
    """Enhanced API caching middleware with Redis backend and intelligent invalidation."""
    
    def __init__(self, app, config: Optional[CacheConfiguration] = None):
        super().__init__(app)
        self.config = config or CacheConfiguration()
        
        # Define cacheable endpoints with specific configurations
        self.cacheable_endpoints = {
            # High-frequency, rarely changing endpoints
            '/health': {'ttl': 60, 'cache_control': 'public, max-age=60'},
            '/version': {'ttl': 3600, 'cache_control': 'public, max-age=3600'},
            
            # Job-related endpoints with different caching strategies
            '/jobs': {'ttl': 120, 'cache_control': 'private, max-age=120'},
            '/jobs/{job_id}': {'ttl': 60, 'cache_control': 'private, max-age=60'},
            '/jobs/{job_id}/download': {'ttl': 300, 'cache_control': 'private, max-age=300'},
            
            # User and stats endpoints
            '/stats': {'ttl': 300, 'cache_control': 'private, max-age=300'},
            '/user/settings': {'ttl': 600, 'cache_control': 'private, max-age=600'},
            
            # Admin endpoints (if needed)
            '/admin/stats': {'ttl': 180, 'cache_control': 'private, max-age=180'},
        }
        
        # Endpoints that should never be cached
        self.non_cacheable_paths: Set[str] = {
            '/transcribe',  # File uploads
            '/auth/login',  # Authentication
            '/auth/logout',
            '/auth/register',
            '/admin/shutdown',
            '/admin/restart',
            '/ws/',  # WebSocket endpoints
        }
        
        # Performance tracking
        self.request_count = 0
        self.cache_hit_count = 0
        
    def _should_cache_request(self, request: Request) -> bool:
        """Determine if request should be cached."""
        # Only cache GET requests
        if request.method != "GET":
            return False
        
        path = request.url.path
        
        # Check explicitly non-cacheable paths
        if any(non_cacheable in path for non_cacheable in self.non_cacheable_paths):
            return False
        
        # Check if path matches cacheable patterns
        for endpoint_pattern in self.cacheable_endpoints:
            if self._path_matches_pattern(path, endpoint_pattern):
                return True
        
        # Default to not caching unknown endpoints
        return False
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches endpoint pattern (supporting {param} placeholders)."""
        if '{' not in pattern:
            return path == pattern
        
        path_parts = path.strip('/').split('/')
        pattern_parts = pattern.strip('/').split('/')
        
        if len(path_parts) != len(pattern_parts):
            return False
        
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                continue  # Parameter match
            elif path_part != pattern_part:
                return False
        
        return True
    
    def _should_cache_response(self, response: Response) -> bool:
        """Determine if response should be cached."""
        # Don't cache error responses
        if response.status_code >= 400:
            return False
        
        # Check cache-control headers
        cache_control = response.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    def _get_endpoint_config(self, path: str) -> Dict[str, any]:
        """Get caching configuration for endpoint."""
        for pattern, config in self.cacheable_endpoints.items():
            if self._path_matches_pattern(path, pattern):
                return config
        
        return {'ttl': self.config.default_ttl, 'cache_control': 'private, max-age=300'}
    
    async def dispatch(self, request: Request, call_next):
        """Handle request with caching logic."""
        self.request_count += 1
        start_time = time.time()
        
        # Skip caching logic if not cacheable
        if not self._should_cache_request(request):
            response = await call_next(request)
            # Add cache headers to indicate no caching
            response.headers["X-Cache"] = "SKIP"
            return response
        
        # Get cache service
        cache_service = await get_cache_service()
        if not cache_service:
            # Fallback to no caching if Redis unavailable
            response = await call_next(request)
            response.headers["X-Cache"] = "UNAVAILABLE"
            return response
        
        # Generate cache key
        cache_key = cache_service._generate_cache_key(request)
        
        # Try to get from cache
        cached_entry = await cache_service.get(cache_key)
        if cached_entry:
            # Cache hit
            self.cache_hit_count += 1
            processing_time = time.time() - start_time
            
            # Create response from cache
            response = Response(
                content=cached_entry.content,
                status_code=cached_entry.status_code,
                headers=cached_entry.headers.copy()
            )
            
            # Add cache headers
            response.headers["X-Cache"] = "HIT"
            response.headers["X-Cache-Hit-Count"] = str(cached_entry.hit_count)
            response.headers["X-Cache-Age"] = str(int((time.time() - cached_entry.created_at.timestamp())))
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
            
            # Set appropriate cache-control headers
            endpoint_config = self._get_endpoint_config(request.url.path)
            response.headers["Cache-Control"] = endpoint_config.get('cache_control', 'private, max-age=300')
            
            logger.debug(f"Cache hit for {request.url.path} (key: {cache_key[:8]}...)")
            return response
        
        # Cache miss - process request
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        # Check if response should be cached
        if self._should_cache_response(response):
            # Read response content for caching
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            content_str = response_body.decode('utf-8')
            
            # Store in cache
            success = await cache_service.set(cache_key, response, request, content_str)
            
            # Recreate response with cached content
            response = Response(
                content=content_str,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
            # Add cache headers
            response.headers["X-Cache"] = "MISS" if success else "STORE-FAILED"
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
            
            # Set cache-control headers
            endpoint_config = self._get_endpoint_config(request.url.path)
            response.headers["Cache-Control"] = endpoint_config.get('cache_control', 'private, max-age=300')
            
            if success:
                logger.debug(f"Cache stored for {request.url.path} (key: {cache_key[:8]}...)")
            else:
                logger.warning(f"Failed to cache response for {request.url.path}")
        else:
            # Response not cacheable
            response.headers["X-Cache"] = "NOT-CACHEABLE"
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
        
        return response
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Get middleware performance statistics."""
        hit_ratio = (self.cache_hit_count / self.request_count) if self.request_count > 0 else 0.0
        
        return {
            'total_requests': self.request_count,
            'cache_hits': self.cache_hit_count,
            'cache_misses': self.request_count - self.cache_hit_count,
            'hit_ratio': hit_ratio,
            'cacheable_endpoints': list(self.cacheable_endpoints.keys()),
            'non_cacheable_paths': list(self.non_cacheable_paths)
        }

class CacheInvalidationHelper:
    """Helper class for intelligent cache invalidation."""
    
    @staticmethod
    async def invalidate_job_cache(job_id: str):
        """Invalidate cache entries related to a specific job."""
        cache_service = await get_cache_service()
        if not cache_service:
            return
        
        # Invalidate specific job caches
        await cache_service.invalidate_by_tag(f"job:{job_id}")
        
        # Invalidate job list caches as they now include updated data
        await cache_service.invalidate_by_tag("jobs")
        
        logger.info(f"Invalidated cache for job {job_id}")
    
    @staticmethod
    async def invalidate_user_cache(user_id: str):
        """Invalidate cache entries related to a specific user."""
        cache_service = await get_cache_service()
        if not cache_service:
            return
        
        await cache_service.invalidate_by_tag(f"user:{user_id}")
        await cache_service.invalidate_by_tag("user_data")
        
        logger.info(f"Invalidated cache for user {user_id}")
    
    @staticmethod
    async def invalidate_stats_cache():
        """Invalidate system stats caches."""
        cache_service = await get_cache_service()
        if not cache_service:
            return
        
        await cache_service.invalidate_by_tag("status_data")
        await cache_service.invalidate_by_pattern("*stats*")
        
        logger.info("Invalidated stats cache")
    
    @staticmethod
    async def warm_common_caches():
        """Warm up commonly accessed cache entries."""
        # This would typically make requests to common endpoints
        # to pre-populate the cache. Implementation depends on application needs.
        logger.info("Cache warming initiated")

# Global cache invalidation helper
cache_invalidator = CacheInvalidationHelper()
