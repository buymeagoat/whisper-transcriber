"""
Rate Limiting Integration Helper
Provides easy integration of enhanced rate limiting into FastAPI applications.
"""

import os
from fastapi import FastAPI
from api.middlewares.enhanced_rate_limiter import EnhancedRateLimitMiddleware
from api.middlewares.rate_limit_config import PRODUCTION_CONFIG, DEVELOPMENT_CONFIG, TEST_CONFIG

def add_rate_limiting(app: FastAPI, environment: str = "production"):
    """
    Add enhanced rate limiting to a FastAPI application.
    
    Args:
        app: The FastAPI application instance
        environment: Environment type ("production", "development", "test")
    """
    # Select configuration based on environment
    if environment == "production":
        config = PRODUCTION_CONFIG
    elif environment == "development":
        config = DEVELOPMENT_CONFIG
    elif environment == "test":
        config = TEST_CONFIG
    else:
        raise ValueError(f"Unknown environment: {environment}")
    
    # Add the middleware
    app.add_middleware(EnhancedRateLimitMiddleware, config=config)
    
    print(f"✅ Enhanced rate limiting enabled for {environment} environment")
    
    # Create logs directory for security events
    os.makedirs("logs", exist_ok=True)
    
    return config

def get_rate_limit_stats():
    """Get current rate limiting statistics (placeholder for future implementation)."""
    return {
        "middleware": "EnhancedRateLimitMiddleware",
        "status": "active",
        "features": [
            "IP-based limiting",
            "User-based limiting", 
            "Endpoint-specific limits",
            "Threat detection",
            "Auto-banning",
            "Progressive delays",
            "Security logging"
        ]
    }
