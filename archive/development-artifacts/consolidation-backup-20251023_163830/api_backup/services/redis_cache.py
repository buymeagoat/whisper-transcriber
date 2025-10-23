"""
Advanced Redis-based caching service for T025 Phase 2: API Response Caching
Implements comprehensive caching with intelligent invalidation strategies.
"""

import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Request, Response
from pydantic import BaseModel

from api.utils.logger import get_system_logger
from api.settings import settings

logger = get_system_logger("redis_cache")

@dataclass
class CacheConfiguration:
    """Advanced cache configuration for different endpoint types."""
    # Redis connection
    redis_url: str = "redis://localhost:6379/0"
    
    # Cache TTL settings (in seconds)
    default_ttl: int = 300  # 5 minutes
    job_status_ttl: int = 60  # 1 minute for job status (frequently changing)
    job_list_ttl: int = 120  # 2 minutes for job lists
    user_data_ttl: int = 600  # 10 minutes for user data
    static_data_ttl: int = 3600  # 1 hour for static data (health, version)
    
    # Cache size and performance
    max_memory_mb: int = 100  # Maximum Redis memory usage
    compression_threshold: int = 1024  # Compress responses larger than 1KB
    
    # Invalidation settings
    enable_smart_invalidation: bool = True
    cache_warming: bool = True
    
    # Performance monitoring
    track_hit_ratio: bool = True
    log_cache_operations: bool = True

@dataclass
class CacheMetrics:
    """Cache performance metrics tracking."""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    invalidations: int = 0
    errors: int = 0
    total_memory_bytes: int = 0
    
    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0

class CacheEntry(BaseModel):
    """Cache entry data structure."""
    content: str
    content_type: str
    status_code: int
    headers: Dict[str, str]
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    tags: List[str] = []

class RedisCacheService:
    """Advanced Redis-based caching service with intelligent invalidation."""
    
    def __init__(self, config: CacheConfiguration):
        self.config = config
        self.redis_pool: Optional[redis.Redis] = None
        self.metrics = CacheMetrics()
        self._key_prefix = "whisper_cache:"
        self._tags_prefix = "whisper_tags:"
        
    async def initialize(self):
        """Initialize Redis connection pool."""
        try:
            self.redis_pool = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.redis_pool.ping()
            logger.info("Redis cache service initialized successfully")
            
            # Set memory policy for cache eviction
            await self.redis_pool.config_set("maxmemory", f"{self.config.max_memory_mb}mb")
            await self.redis_pool.config_set("maxmemory-policy", "allkeys-lru")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.redis_pool = None
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_pool:
            await self.redis_pool.close()
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request."""
        key_components = [
            request.method,
            request.url.path,
            request.url.query
        ]
        
        # Include user context for personalized caching
        if hasattr(request.state, 'user') and request.state.user:
            key_components.append(f"user:{request.state.user.get('id', 'anonymous')}")
        
        # Include relevant headers for content negotiation
        for header in ['accept', 'accept-language', 'accept-encoding']:
            if header in request.headers:
                key_components.append(f"{header}:{request.headers[header]}")
        
        key_string = "|".join(key_components)
        cache_key = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"{self._key_prefix}{cache_key}"
    
    def _determine_ttl(self, request: Request) -> int:
        """Determine appropriate TTL based on request type."""
        path = request.url.path
        
        # Static/rarely changing endpoints
        if path in ['/health', '/version', '/stats']:
            return self.config.static_data_ttl
        
        # Job-related endpoints with different update frequencies
        if path.startswith('/jobs'):
            if path.endswith('/download'):
                return self.config.default_ttl * 4  # Download links can be cached longer
            elif '/jobs/' in path and not path.endswith('/jobs'):
                return self.config.job_status_ttl  # Individual job status changes frequently
            else:
                return self.config.job_list_ttl  # Job lists change moderately
        
        # User data
        if path.startswith('/user'):
            return self.config.user_data_ttl
        
        return self.config.default_ttl
    
    def _extract_cache_tags(self, request: Request, response_content: str) -> List[str]:
        """Extract tags for intelligent cache invalidation."""
        tags = []
        path = request.url.path
        
        # Add path-based tags
        if path.startswith('/jobs'):
            tags.append('jobs')
            
            # Extract job ID if present
            parts = path.split('/')
            if len(parts) >= 3 and parts[1] == 'jobs':
                job_id = parts[2]
                if job_id != 'jobs':  # Avoid tagging list endpoints
                    tags.append(f'job:{job_id}')
        
        if path.startswith('/user'):
            tags.append('user_data')
            if hasattr(request.state, 'user') and request.state.user:
                tags.append(f"user:{request.state.user.get('id')}")
        
        # Add status-based tags
        if 'status' in response_content.lower():
            tags.append('status_data')
        
        return tags
    
    async def get(self, cache_key: str) -> Optional[CacheEntry]:
        """Retrieve entry from cache."""
        if not self.redis_pool:
            return None
        
        try:
            data = await self.redis_pool.get(cache_key)
            if not data:
                self.metrics.misses += 1
                return None
            
            entry_dict = json.loads(data)
            entry = CacheEntry(**entry_dict)
            
            # Check expiration
            if datetime.now() >= entry.expires_at:
                await self.redis_pool.delete(cache_key)
                self.metrics.misses += 1
                return None
            
            # Update hit count
            entry.hit_count += 1
            await self.redis_pool.set(cache_key, entry.json(), ex=int((entry.expires_at - datetime.now()).total_seconds()))
            
            self.metrics.hits += 1
            
            if self.config.log_cache_operations:
                logger.debug(f"Cache hit: {cache_key}")
            
            return entry
            
        except Exception as e:
            logger.error(f"Cache get error for {cache_key}: {e}")
            self.metrics.errors += 1
            return None
    
    async def set(self, cache_key: str, response: Response, request: Request, content: str) -> bool:
        """Store response in cache."""
        if not self.redis_pool:
            return False
        
        try:
            ttl = self._determine_ttl(request)
            expires_at = datetime.now() + timedelta(seconds=ttl)
            tags = self._extract_cache_tags(request, content)
            
            # Compress large responses
            if len(content) > self.config.compression_threshold:
                # In production, you might want to use gzip compression here
                logger.debug(f"Large response cached ({len(content)} bytes): {cache_key}")
            
            entry = CacheEntry(
                content=content,
                content_type=response.headers.get("content-type", "application/json"),
                status_code=response.status_code,
                headers=dict(response.headers),
                created_at=datetime.now(),
                expires_at=expires_at,
                tags=tags
            )
            
            # Store main cache entry
            await self.redis_pool.set(cache_key, entry.json(), ex=ttl)
            
            # Store tag mappings for invalidation
            for tag in tags:
                tag_key = f"{self._tags_prefix}{tag}"
                # Note: sadd behavior varies by Redis version  
                await self.redis_pool.sadd(tag_key, cache_key)  # type: ignore
                await self.redis_pool.expire(tag_key, ttl + 60)  # Keep tags slightly longer
            
            self.metrics.sets += 1
            
            if self.config.log_cache_operations:
                logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s, Tags: {tags})")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {cache_key}: {e}")
            self.metrics.errors += 1
            return False
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with a specific tag."""
        if not self.redis_pool:
            return 0
        
        try:
            tag_key = f"{self._tags_prefix}{tag}"
            # Note: smembers behavior varies by Redis version
            cache_keys = await self.redis_pool.smembers(tag_key)  # type: ignore
            
            if cache_keys:
                # Convert to list to handle different return types
                cache_keys_list = list(cache_keys) if hasattr(cache_keys, '__iter__') else []
                if cache_keys_list:
                    # Delete cache entries
                    deleted = await self.redis_pool.delete(*cache_keys_list)
                    # Delete tag set
                    await self.redis_pool.delete(tag_key)
                
                self.metrics.invalidations += deleted
                
                if self.config.log_cache_operations:
                    logger.info(f"Invalidated {deleted} cache entries for tag: {tag}")
                
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation error for tag {tag}: {e}")
            self.metrics.errors += 1
            return 0
    
    async def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        if not self.redis_pool:
            return 0
        
        try:
            pattern_key = f"{self._key_prefix}{pattern}"
            cache_keys = []
            
            # Scan for matching keys
            async for key in self.redis_pool.scan_iter(match=pattern_key, count=100):
                cache_keys.append(key)
            
            if cache_keys:
                deleted = await self.redis_pool.delete(*cache_keys)
                self.metrics.invalidations += deleted
                
                if self.config.log_cache_operations:
                    logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
                
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for {pattern}: {e}")
            self.metrics.errors += 1
            return 0
    
    async def clear_all(self) -> bool:
        """Clear all cache entries."""
        if not self.redis_pool:
            return False
        
        try:
            # Clear cache entries
            cache_keys = []
            async for key in self.redis_pool.scan_iter(match=f"{self._key_prefix}*", count=100):
                cache_keys.append(key)
            
            # Clear tag mappings
            tag_keys = []
            async for key in self.redis_pool.scan_iter(match=f"{self._tags_prefix}*", count=100):
                tag_keys.append(key)
            
            all_keys = cache_keys + tag_keys
            if all_keys:
                await self.redis_pool.delete(*all_keys)
            
            cleared_count = len(all_keys)
            self.metrics.invalidations += cleared_count
            
            logger.info(f"Cleared all cache entries: {cleared_count} keys deleted")
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            self.metrics.errors += 1
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        memory_info = {}
        
        if self.redis_pool:
            try:
                info = await self.redis_pool.info('memory')
                memory_info = {
                    'used_memory': info.get('used_memory', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'used_memory_peak': info.get('used_memory_peak', 0),
                    'total_system_memory': info.get('total_system_memory', 0)
                }
            except Exception as e:
                logger.error(f"Failed to get Redis memory info: {e}")
        
        return {
            'hit_ratio': self.metrics.hit_ratio,
            'hits': self.metrics.hits,
            'misses': self.metrics.misses,
            'sets': self.metrics.sets,
            'invalidations': self.metrics.invalidations,
            'errors': self.metrics.errors,
            'memory_info': memory_info,
            'config': asdict(self.config)
        }

# Global cache service instance
cache_service: Optional[RedisCacheService] = None

async def get_cache_service() -> Optional[RedisCacheService]:
    """Get the global cache service instance."""
    return cache_service

async def initialize_cache_service(config: Optional[CacheConfiguration] = None):
    """Initialize the global cache service."""
    global cache_service
    
    if config is None:
        config = CacheConfiguration()
    
    cache_service = RedisCacheService(config)
    await cache_service.initialize()
    
    logger.info("Redis cache service initialized globally")

async def cleanup_cache_service():
    """Cleanup the global cache service."""
    global cache_service
    
    if cache_service:
        await cache_service.close()
        cache_service = None
        
    logger.info("Redis cache service cleaned up")

@asynccontextmanager
async def cache_service_context(config: Optional[CacheConfiguration] = None):
    """Context manager for cache service lifecycle."""
    await initialize_cache_service(config)
    try:
        yield cache_service
    finally:
        await cleanup_cache_service()
