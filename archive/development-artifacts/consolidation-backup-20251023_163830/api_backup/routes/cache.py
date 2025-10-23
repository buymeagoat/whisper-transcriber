"""Cache management routes for administrative control."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ..routes.auth import verify_token

# Create router instance
router = APIRouter(tags=["cache"])

# Global reference to cache middleware
_cache_middleware: Optional[Any] = None

def set_cache_middleware(middleware):
    """Set the cache middleware instance for admin operations."""
    global _cache_middleware
    _cache_middleware = middleware

# Response models
class CacheStats(BaseModel):
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    hit_rate: float
    oldest_entry: str
    newest_entry: str

class CacheEntry(BaseModel):
    key: str
    size_bytes: int
    created_at: str
    last_accessed: str
    access_count: int
    ttl_seconds: int

class CacheOperation(BaseModel):
    success: bool
    message: str
    affected_keys: List[str] = []

# Mock cache store
CACHE_STORE: Dict[str, Dict[str, Any]] = {}
CACHE_STATS = {
    "hit_count": 0,
    "miss_count": 0
}

@router.get("/stats", response_model=CacheStats)
async def get_cache_stats(current_user: dict = Depends(verify_token)):
    """Get cache statistics and performance metrics."""
    total_entries = len(CACHE_STORE)
    total_size = sum(entry.get("size_bytes", 0) for entry in CACHE_STORE.values())
    
    hit_count = CACHE_STATS["hit_count"]
    miss_count = CACHE_STATS["miss_count"]
    total_requests = hit_count + miss_count
    hit_rate = (hit_count / total_requests) if total_requests > 0 else 0.0
    
    # Find oldest and newest entries
    entries = list(CACHE_STORE.values())
    if entries:
        oldest_entry = min(entries, key=lambda x: x.get("created_at", ""))["key"]
        newest_entry = max(entries, key=lambda x: x.get("created_at", ""))["key"]
    else:
        oldest_entry = newest_entry = "None"
    
    return CacheStats(
        total_entries=total_entries,
        total_size_bytes=total_size,
        hit_count=hit_count,
        miss_count=miss_count,
        hit_rate=hit_rate,
        oldest_entry=oldest_entry,
        newest_entry=newest_entry
    )

@router.get("/entries", response_model=List[CacheEntry])
async def list_cache_entries(
    limit: int = 100,
    current_user: dict = Depends(verify_token)
):
    """List all cache entries with metadata."""
    entries = []
    for key, data in list(CACHE_STORE.items())[:limit]:
        entries.append(CacheEntry(
            key=key,
            size_bytes=data.get("size_bytes", 0),
            created_at=data.get("created_at", "unknown"),
            last_accessed=data.get("last_accessed", "unknown"),
            access_count=data.get("access_count", 0),
            ttl_seconds=data.get("ttl_seconds", -1)
        ))
    return entries

@router.get("/entries/{key}")
async def get_cache_entry(
    key: str,
    current_user: dict = Depends(verify_token)
):
    """Get a specific cache entry by key."""
    if key not in CACHE_STORE:
        CACHE_STATS["miss_count"] += 1
        raise HTTPException(status_code=404, detail="Cache entry not found")
    
    CACHE_STATS["hit_count"] += 1
    entry = CACHE_STORE[key]
    entry["access_count"] = entry.get("access_count", 0) + 1
    entry["last_accessed"] = "2024-01-01T12:00:00Z"  # Would be current time in production
    
    return {
        "key": key,
        "value": entry.get("value"),
        "metadata": {
            "size_bytes": entry.get("size_bytes", 0),
            "created_at": entry.get("created_at"),
            "last_accessed": entry.get("last_accessed"),
            "access_count": entry.get("access_count", 0),
            "ttl_seconds": entry.get("ttl_seconds", -1)
        }
    }

@router.delete("/entries/{key}", response_model=CacheOperation)
async def delete_cache_entry(
    key: str,
    current_user: dict = Depends(verify_token)
):
    """Delete a specific cache entry."""
    if key not in CACHE_STORE:
        raise HTTPException(status_code=404, detail="Cache entry not found")
    
    del CACHE_STORE[key]
    return CacheOperation(
        success=True,
        message=f"Cache entry '{key}' deleted successfully",
        affected_keys=[key]
    )

@router.post("/clear", response_model=CacheOperation)
async def clear_cache(
    pattern: str = "*",
    current_user: dict = Depends(verify_token)
):
    """Clear cache entries matching a pattern."""
    if pattern == "*":
        # Clear all entries
        keys_to_delete = list(CACHE_STORE.keys())
        CACHE_STORE.clear()
        message = "All cache entries cleared"
    else:
        # Clear entries matching pattern (simple contains match)
        keys_to_delete = [key for key in CACHE_STORE.keys() if pattern in key]
        for key in keys_to_delete:
            del CACHE_STORE[key]
        message = f"Cleared {len(keys_to_delete)} entries matching pattern '{pattern}'"
    
    return CacheOperation(
        success=True,
        message=message,
        affected_keys=keys_to_delete
    )

@router.post("/warm", response_model=CacheOperation)
async def warm_cache(
    keys: List[str] = [],
    current_user: dict = Depends(verify_token)
):
    """Warm the cache with specified keys or common patterns."""
    if not keys:
        # Default warm-up keys
        keys = ["user_sessions", "job_queue_status", "system_config"]
    
    warmed_keys = []
    for key in keys:
        if key not in CACHE_STORE:
            # Simulate caching common data
            CACHE_STORE[key] = {
                "key": key,
                "value": f"warmed_data_for_{key}",
                "size_bytes": len(key) * 10,  # Mock size
                "created_at": "2024-01-01T12:00:00Z",
                "last_accessed": "2024-01-01T12:00:00Z",
                "access_count": 0,
                "ttl_seconds": 3600
            }
            warmed_keys.append(key)
    
    return CacheOperation(
        success=True,
        message=f"Cache warmed with {len(warmed_keys)} entries",
        affected_keys=warmed_keys
    )

@router.get("/health")
async def cache_health_check(current_user: dict = Depends(verify_token)):
    """Check cache system health."""
    return {
        "status": "healthy",
        "cache_size": len(CACHE_STORE),
        "memory_usage": "low",  # Would be actual memory usage in production
        "last_cleanup": "2024-01-01T12:00:00Z"
    }

# Initialize with some sample cache entries
if not CACHE_STORE:
    sample_entries = {
        "user_sessions": {"value": "active_sessions_data", "size_bytes": 1024},
        "job_queue_status": {"value": "queue_statistics", "size_bytes": 512},
        "system_config": {"value": "configuration_data", "size_bytes": 256}
    }
    
    for key, data in sample_entries.items():
        CACHE_STORE[key] = {
            "key": key,
            "value": data["value"],
            "size_bytes": data["size_bytes"],
            "created_at": "2024-01-01T12:00:00Z",
            "last_accessed": "2024-01-01T12:00:00Z",
            "access_count": 0,
            "ttl_seconds": 3600
        }