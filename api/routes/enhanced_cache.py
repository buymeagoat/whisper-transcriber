"""
Enhanced cache management routes for T025 Phase 2: API Response Caching
Provides comprehensive cache administration and monitoring capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

from api.routes.auth import get_current_admin_user as verify_token
from api.services.redis_cache import get_cache_service
from api.services.cache_hooks import (
    cache_performance_monitor,
    manual_cache_invalidation,
    manual_cache_clear,
    get_cache_health,
    job_cache_manager,
    cache_warming_service
)
from api.middlewares.enhanced_cache import cache_invalidator

router = APIRouter(prefix="/admin/cache", tags=["cache", "admin"])

# Enhanced response models
class EnhancedCacheStats(BaseModel):
    hit_ratio: float
    total_hits: int
    total_misses: int
    total_sets: int
    total_invalidations: int
    total_errors: int
    memory_info: Dict[str, Any]
    health_score: int
    recommendations: List[str]

class CacheHealthStatus(BaseModel):
    status: str
    healthy: bool
    message: str
    test_successful: Optional[bool] = None
    redis_info: Optional[Dict[str, Any]] = None

class CacheOperation(BaseModel):
    success: bool
    message: str
    affected_keys: List[str] = []
    operation_time: float

class CacheInvalidationRequest(BaseModel):
    patterns: List[str]
    reason: Optional[str] = "Manual invalidation"

class CacheWarmingRequest(BaseModel):
    endpoints: List[str]
    priority: str = "normal"  # normal, high, low

@router.get("/health", response_model=CacheHealthStatus)
async def get_cache_health_status(current_user: dict = Depends(verify_token)):
    """Get comprehensive cache service health status."""
    health_status = await get_cache_health()
    
    # Add Redis-specific information if available
    cache_service = await get_cache_service()
    if cache_service and cache_service.redis_pool:
        try:
            redis_info = await cache_service.redis_pool.info()
            health_status["redis_info"] = {
                "version": redis_info.get("redis_version"),
                "connected_clients": redis_info.get("connected_clients"),
                "uptime_in_seconds": redis_info.get("uptime_in_seconds"),
                "used_memory_human": redis_info.get("used_memory_human"),
                "keyspace_hits": redis_info.get("keyspace_hits"),
                "keyspace_misses": redis_info.get("keyspace_misses")
            }
        except Exception as e:
            health_status["redis_info"] = {"error": str(e)}
    
    return CacheHealthStatus(**health_status)

@router.get("/stats", response_model=EnhancedCacheStats)
async def get_enhanced_cache_stats(current_user: dict = Depends(verify_token)):
    """Get comprehensive cache statistics and performance metrics."""
    performance_data = await cache_performance_monitor.analyze_performance()
    
    if 'metrics' not in performance_data:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    metrics = performance_data['metrics']
    recommendations = performance_data.get('recommendations', [])
    health_score = performance_data.get('health_score', 0)
    
    return EnhancedCacheStats(
        hit_ratio=metrics.get('hit_ratio', 0.0),
        total_hits=metrics.get('hits', 0),
        total_misses=metrics.get('misses', 0),
        total_sets=metrics.get('sets', 0),
        total_invalidations=metrics.get('invalidations', 0),
        total_errors=metrics.get('errors', 0),
        memory_info=metrics.get('memory_info', {}),
        health_score=health_score,
        recommendations=recommendations
    )

@router.get("/performance")
async def get_cache_performance_analysis(current_user: dict = Depends(verify_token)):
    """Get detailed cache performance analysis and optimization recommendations."""
    return await cache_performance_monitor.get_cache_statistics()

@router.post("/invalidate", response_model=CacheOperation)
async def invalidate_cache_patterns(
    request: CacheInvalidationRequest,
    current_user: dict = Depends(verify_token)
):
    """Invalidate cache entries matching specified patterns."""
    import time
    start_time = time.time()
    
    try:
        results = await manual_cache_invalidation(request.patterns)
        total_affected = sum(results.values())
        
        operation_time = time.time() - start_time
        
        return CacheOperation(
            success=True,
            message=f"Invalidated {total_affected} cache entries for patterns: {', '.join(request.patterns)}",
            affected_keys=[f"{pattern}:{count}" for pattern, count in results.items()],
            operation_time=operation_time
        )
    except Exception as e:
        operation_time = time.time() - start_time
        return CacheOperation(
            success=False,
            message=f"Cache invalidation failed: {str(e)}",
            affected_keys=[],
            operation_time=operation_time
        )

@router.post("/invalidate/job/{job_id}", response_model=CacheOperation)
async def invalidate_job_cache(
    job_id: str,
    current_user: dict = Depends(verify_token)
):
    """Invalidate cache entries for a specific job."""
    import time
    start_time = time.time()
    
    try:
        await cache_invalidator.invalidate_job_cache(job_id)
        operation_time = time.time() - start_time
        
        return CacheOperation(
            success=True,
            message=f"Invalidated cache for job {job_id}",
            affected_keys=[f"job:{job_id}", "jobs"],
            operation_time=operation_time
        )
    except Exception as e:
        operation_time = time.time() - start_time
        return CacheOperation(
            success=False,
            message=f"Job cache invalidation failed: {str(e)}",
            affected_keys=[],
            operation_time=operation_time
        )

@router.post("/invalidate/user/{user_id}", response_model=CacheOperation)
async def invalidate_user_cache(
    user_id: str,
    current_user: dict = Depends(verify_token)
):
    """Invalidate cache entries for a specific user."""
    import time
    start_time = time.time()
    
    try:
        await cache_invalidator.invalidate_user_cache(user_id)
        operation_time = time.time() - start_time
        
        return CacheOperation(
            success=True,
            message=f"Invalidated cache for user {user_id}",
            affected_keys=[f"user:{user_id}", "user_data"],
            operation_time=operation_time
        )
    except Exception as e:
        operation_time = time.time() - start_time
        return CacheOperation(
            success=False,
            message=f"User cache invalidation failed: {str(e)}",
            affected_keys=[],
            operation_time=operation_time
        )

@router.post("/clear", response_model=CacheOperation)
async def clear_entire_cache(
    confirm: bool = Query(False, description="Confirm cache clearing"),
    current_user: dict = Depends(verify_token)
):
    """Clear entire cache (requires confirmation)."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Cache clearing requires confirmation parameter: ?confirm=true"
        )
    
    import time
    start_time = time.time()
    
    try:
        success = await manual_cache_clear()
        operation_time = time.time() - start_time
        
        if success:
            return CacheOperation(
                success=True,
                message="Entire cache cleared successfully",
                affected_keys=["*"],
                operation_time=operation_time
            )
        else:
            return CacheOperation(
                success=False,
                message="Cache clearing failed",
                affected_keys=[],
                operation_time=operation_time
            )
    except Exception as e:
        operation_time = time.time() - start_time
        return CacheOperation(
            success=False,
            message=f"Cache clearing failed: {str(e)}",
            affected_keys=[],
            operation_time=operation_time
        )

@router.post("/warm", response_model=CacheOperation)
async def warm_cache(
    request: CacheWarmingRequest,
    current_user: dict = Depends(verify_token)
):
    """Warm up cache for specified endpoints."""
    import time
    start_time = time.time()
    
    try:
        # Perform cache warming based on request
        if "health" in request.endpoints:
            await cache_warming_service.warm_health_endpoint()
        
        if "jobs" in request.endpoints:
            await cache_warming_service.warm_job_lists()
        
        if "stats" in request.endpoints:
            await cache_warming_service.warm_user_stats([])
        
        operation_time = time.time() - start_time
        
        return CacheOperation(
            success=True,
            message=f"Cache warming completed for endpoints: {', '.join(request.endpoints)}",
            affected_keys=request.endpoints,
            operation_time=operation_time
        )
    except Exception as e:
        operation_time = time.time() - start_time
        return CacheOperation(
            success=False,
            message=f"Cache warming failed: {str(e)}",
            affected_keys=[],
            operation_time=operation_time
        )

@router.get("/keys")
async def list_cache_keys(
    pattern: str = Query("*", description="Pattern to match cache keys"),
    limit: int = Query(100, description="Maximum number of keys to return"),
    current_user: dict = Depends(verify_token)
):
    """List cache keys matching a pattern."""
    cache_service = await get_cache_service()
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    try:
        keys = []
        count = 0
        
        async for key in cache_service.redis_pool.scan_iter(match=f"whisper_cache:{pattern}", count=10):
            if count >= limit:
                break
            keys.append(key.replace("whisper_cache:", ""))
            count += 1
        
        return {
            "keys": keys,
            "total_found": count,
            "limit": limit,
            "pattern": pattern
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cache keys: {str(e)}")

@router.get("/entry/{cache_key}")
async def get_cache_entry_details(
    cache_key: str,
    current_user: dict = Depends(verify_token)
):
    """Get details of a specific cache entry."""
    cache_service = await get_cache_service()
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    
    full_key = f"whisper_cache:{cache_key}"
    
    try:
        entry = await cache_service.get(full_key)
        if not entry:
            raise HTTPException(status_code=404, detail="Cache entry not found")
        
        return {
            "key": cache_key,
            "content_preview": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
            "content_length": len(entry.content),
            "content_type": entry.content_type,
            "status_code": entry.status_code,
            "created_at": entry.created_at.isoformat(),
            "expires_at": entry.expires_at.isoformat(),
            "hit_count": entry.hit_count,
            "tags": entry.tags,
            "headers": entry.headers
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache entry: {str(e)}")

@router.get("/monitor/realtime")
async def get_realtime_cache_metrics(current_user: dict = Depends(verify_token)):
    """Get real-time cache metrics for monitoring dashboards."""
    cache_service = await get_cache_service()
    if not cache_service:
        return {"status": "unavailable", "timestamp": datetime.now().isoformat()}
    
    try:
        metrics = await cache_service.get_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "active",
            "metrics": {
                "hit_ratio": metrics.get('hit_ratio', 0.0),
                "operations_per_second": {
                    "hits": metrics.get('hits', 0),
                    "misses": metrics.get('misses', 0),
                    "sets": metrics.get('sets', 0)
                },
                "memory": metrics.get('memory_info', {}),
                "error_rate": metrics.get('errors', 0) / max(1, metrics.get('hits', 0) + metrics.get('misses', 0))
            },
            "health_indicators": {
                "redis_connected": bool(cache_service.redis_pool),
                "memory_usage_ok": metrics.get('memory_info', {}).get('used_memory', 0) < 80 * 1024 * 1024,  # 80MB threshold
                "error_rate_ok": metrics.get('errors', 0) < 10
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
