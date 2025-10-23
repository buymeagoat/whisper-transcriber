"""
Cache invalidation hooks for automatic cache management in T025 Phase 2.
Provides automatic cache invalidation when data changes.
"""

import asyncio
from typing import Optional, List, Dict, Any
from functools import wraps

from api.services.redis_cache import get_cache_service
from api.middlewares.enhanced_cache import cache_invalidator
from api.utils.logger import get_system_logger

logger = get_system_logger("cache_hooks")

class CacheInvalidationHooks:
    """Automatic cache invalidation hooks for data mutations."""
    
    @staticmethod
    def invalidate_on_job_update(job_id: str):
        """Decorator to invalidate job-related caches when job data changes."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                # Invalidate after successful update
                await cache_invalidator.invalidate_job_cache(job_id)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                # Schedule invalidation for sync functions
                asyncio.create_task(cache_invalidator.invalidate_job_cache(job_id))
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    @staticmethod
    def invalidate_on_user_update(user_id: str):
        """Decorator to invalidate user-related caches when user data changes."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                await cache_invalidator.invalidate_user_cache(user_id)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                asyncio.create_task(cache_invalidator.invalidate_user_cache(user_id))
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    @staticmethod
    def invalidate_stats_cache():
        """Decorator to invalidate stats caches when system data changes."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                await cache_invalidator.invalidate_stats_cache()
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                asyncio.create_task(cache_invalidator.invalidate_stats_cache())
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

# Event-based cache invalidation for job status changes
class JobStatusCacheManager:
    """Manages cache invalidation for job status changes."""
    
    def __init__(self):
        self.status_change_callbacks = []
    
    async def on_job_status_change(self, job_id: str, old_status: str, new_status: str):
        """Handle job status change for cache invalidation."""
        logger.debug(f"Job {job_id} status changed: {old_status} -> {new_status}")
        
        # Invalidate job-specific cache
        await cache_invalidator.invalidate_job_cache(job_id)
        
        # Invalidate stats cache if status affects system metrics
        if new_status in ['completed', 'failed', 'pending']:
            await cache_invalidator.invalidate_stats_cache()
        
        # Execute registered callbacks
        for callback in self.status_change_callbacks:
            try:
                await callback(job_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Cache callback error: {e}")
    
    def register_status_change_callback(self, callback):
        """Register a callback for job status changes."""
        self.status_change_callbacks.append(callback)
    
    async def job_created(self, job_id: str, job_data: Dict[str, Any]):
        """Handle new job creation."""
        logger.debug(f"New job created: {job_id}")
        
        # Invalidate job list caches
        await cache_invalidator.invalidate_job_cache("all")
        await cache_invalidator.invalidate_stats_cache()
    
    async def job_deleted(self, job_id: str):
        """Handle job deletion."""
        logger.debug(f"Job deleted: {job_id}")
        
        # Invalidate specific job cache and lists
        await cache_invalidator.invalidate_job_cache(job_id)
        await cache_invalidator.invalidate_stats_cache()

# Global job cache manager
job_cache_manager = JobStatusCacheManager()

# Cache warming strategies
class CacheWarmingService:
    """Service for proactive cache warming."""
    
    def __init__(self):
        self.warming_tasks = []
    
    async def warm_health_endpoint(self):
        """Warm up health endpoint cache."""
        try:
            # In a real implementation, this would make an internal request
            # to the health endpoint to populate the cache
            logger.debug("Warming health endpoint cache")
        except Exception as e:
            logger.error(f"Cache warming failed for health endpoint: {e}")
    
    async def warm_job_lists(self, user_id: Optional[str] = None):
        """Warm up job list caches for active users."""
        try:
            # This would fetch job lists for recently active users
            # to ensure commonly accessed data is cached
            logger.debug(f"Warming job list cache for user: {user_id or 'all'}")
        except Exception as e:
            logger.error(f"Cache warming failed for job lists: {e}")
    
    async def warm_user_stats(self, user_ids: List[str]):
        """Warm up user statistics caches."""
        try:
            for user_id in user_ids:
                # Fetch user stats to populate cache
                logger.debug(f"Warming stats cache for user: {user_id}")
        except Exception as e:
            logger.error(f"Cache warming failed for user stats: {e}")
    
    async def scheduled_warming(self):
        """Perform scheduled cache warming."""
        logger.info("Starting scheduled cache warming")
        
        # Warm high-frequency endpoints
        await self.warm_health_endpoint()
        
        # Warm job-related caches during off-peak hours
        # Implementation would check current time and load
        
        logger.info("Scheduled cache warming completed")

# Global cache warming service
cache_warming_service = CacheWarmingService()

# Cache performance monitoring
class CachePerformanceMonitor:
    """Monitor cache performance and provide optimization recommendations."""
    
    def __init__(self):
        self.performance_history = []
        self.recommendations = []
    
    async def analyze_performance(self) -> Dict[str, Any]:
        """Analyze cache performance and provide insights."""
        cache_service = await get_cache_service()
        if not cache_service:
            return {'status': 'unavailable'}
        
        metrics = await cache_service.get_metrics()
        
        # Analyze hit ratio
        hit_ratio = metrics.get('hit_ratio', 0.0)
        recommendations = []
        
        if hit_ratio < 0.3:
            recommendations.append("Low hit ratio detected. Consider increasing TTL for static endpoints.")
        elif hit_ratio > 0.8:
            recommendations.append("Excellent hit ratio. Current caching strategy is effective.")
        
        # Analyze memory usage
        memory_info = metrics.get('memory_info', {})
        used_memory = memory_info.get('used_memory', 0)
        if used_memory > 50 * 1024 * 1024:  # 50MB
            recommendations.append("High memory usage detected. Consider implementing cache eviction policies.")
        
        # Analyze error rate
        total_ops = metrics.get('hits', 0) + metrics.get('misses', 0) + metrics.get('sets', 0)
        error_rate = metrics.get('errors', 0) / total_ops if total_ops > 0 else 0
        if error_rate > 0.05:  # 5% error rate
            recommendations.append("High cache error rate detected. Check Redis connection stability.")
        
        return {
            'metrics': metrics,
            'recommendations': recommendations,
            'health_score': min(100, int(hit_ratio * 100 + (1 - error_rate) * 50))
        }
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        cache_service = await get_cache_service()
        if not cache_service:
            return {'status': 'Cache service unavailable'}
        
        metrics = await cache_service.get_metrics()
        performance_analysis = await self.analyze_performance()
        
        return {
            'cache_metrics': metrics,
            'performance_analysis': performance_analysis,
            'service_status': 'active' if cache_service else 'inactive'
        }

# Global performance monitor
cache_performance_monitor = CachePerformanceMonitor()

# Utility functions for manual cache operations
async def manual_cache_invalidation(patterns: List[str]) -> Dict[str, int]:
    """Manually invalidate cache entries by patterns."""
    cache_service = await get_cache_service()
    if not cache_service:
        return {'error': 'Cache service unavailable'}
    
    results = {}
    for pattern in patterns:
        count = await cache_service.invalidate_by_pattern(pattern)
        results[pattern] = count
    
    return results

async def manual_cache_clear() -> bool:
    """Manually clear entire cache."""
    cache_service = await get_cache_service()
    if not cache_service:
        return False
    
    return await cache_service.clear_all()

async def get_cache_health() -> Dict[str, Any]:
    """Get cache service health status."""
    cache_service = await get_cache_service()
    if not cache_service:
        return {
            'status': 'unavailable',
            'healthy': False,
            'message': 'Cache service not initialized'
        }
    
    try:
        # Test basic operations
        test_key = "health_check_test"
        await cache_service.redis_pool.set(test_key, "test", ex=5)
        test_value = await cache_service.redis_pool.get(test_key)
        await cache_service.redis_pool.delete(test_key)
        
        return {
            'status': 'healthy',
            'healthy': True,
            'message': 'Cache service operational',
            'test_successful': test_value == "test"
        }
    except Exception as e:
        return {
            'status': 'error',
            'healthy': False,
            'message': f'Cache service error: {str(e)}'
        }
