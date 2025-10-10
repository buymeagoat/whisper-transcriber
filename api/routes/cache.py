"""
Cache management routes for administrators
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from api.routes.auth import require_admin
from api.models import User


router = APIRouter()

# Global reference to cache middleware (will be set during app startup)
_cache_middleware = None


def set_cache_middleware(middleware):
    """Set the cache middleware instance for admin operations"""
    global _cache_middleware
    _cache_middleware = middleware


@router.get("/cache/stats")
async def get_cache_statistics(
    admin_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get cache statistics and performance metrics
    
    Requires admin privileges.
    """
    if not _cache_middleware:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache middleware not available"
        )
    
    try:
        stats = await _cache_middleware.get_cache_stats()
        
        # Add configuration information
        config_info = {
            "default_ttl": _cache_middleware.config.default_ttl,
            "max_cache_size": _cache_middleware.config.max_cache_size,
            "caching_enabled": _cache_middleware.config.enable_caching,
            "cached_endpoints": list(_cache_middleware.config.endpoint_rules.keys()),
            "no_cache_endpoints": list(_cache_middleware.config.no_cache_endpoints),
            "user_specific_endpoints": list(_cache_middleware.config.user_specific_endpoints)
        }
        
        return {
            "cache_stats": stats,
            "configuration": config_info,
            "status": "operational"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(
    admin_user: User = Depends(require_admin)
) -> Dict[str, str]:
    """
    Clear all cached responses
    
    Requires admin privileges.
    """
    if not _cache_middleware:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache middleware not available"
        )
    
    try:
        await _cache_middleware.clear_cache()
        return {
            "message": "Cache cleared successfully",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/cache/config")
async def get_cache_configuration(
    admin_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get detailed cache configuration
    
    Requires admin privileges.
    """
    if not _cache_middleware:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache middleware not available"
        )
    
    config = _cache_middleware.config
    
    return {
        "caching_enabled": config.enable_caching,
        "default_ttl_seconds": config.default_ttl,
        "max_cache_size": config.max_cache_size,
        "endpoint_rules": [
            {
                "endpoint": endpoint,
                "ttl_seconds": rules.get("ttl", config.default_ttl),
                "methods": rules.get("methods", ["GET"]),
                "description": f"Cached for {rules.get('ttl', config.default_ttl)} seconds"
            }
            for endpoint, rules in config.endpoint_rules.items()
        ],
        "no_cache_endpoints": [
            {
                "endpoint": endpoint,
                "reason": "Security or dynamic content"
            }
            for endpoint in config.no_cache_endpoints
        ],
        "user_specific_endpoints": [
            {
                "endpoint": endpoint,
                "description": "Cached per user with user ID in cache key"
            }
            for endpoint in config.user_specific_endpoints
        ]
    }
