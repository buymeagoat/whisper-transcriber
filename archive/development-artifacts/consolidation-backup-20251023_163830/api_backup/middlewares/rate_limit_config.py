"""
Enhanced Rate Limiting Configuration
Customize rate limits for different endpoints and security requirements.
"""

from api.middlewares.enhanced_rate_limiter import EnhancedRateLimitConfig, SecurityRateLimit

# Production rate limiting configuration
PRODUCTION_CONFIG = EnhancedRateLimitConfig(
    # Global limits (per IP) - More restrictive for production
    global_limit=SecurityRateLimit(60, 60, ban_threshold=15, ban_duration=1800),  # 60 req/min
    
    # Per-user limits (authenticated requests)
    user_limit=SecurityRateLimit(300, 3600),  # 300 req/hour for authenticated users
    
    # Enhanced endpoint limits
    endpoint_limits={
        # Authentication endpoints (very strict)
        "/token": SecurityRateLimit(3, 300, ban_threshold=5, ban_duration=1800),  # 3 per 5 min
        "/login": SecurityRateLimit(3, 300, ban_threshold=5, ban_duration=1800),
        "/register": SecurityRateLimit(1, 3600, ban_threshold=3, ban_duration=3600),  # 1 per hour
        "/change-password": SecurityRateLimit(2, 900, ban_threshold=3),  # 2 per 15 min
        
        # Admin endpoints (highly restricted)
        "/admin/*": SecurityRateLimit(20, 60, ban_threshold=10),
        "/admin/delete": SecurityRateLimit(3, 900, ban_threshold=3),
        "/admin/cleanup": SecurityRateLimit(1, 3600, ban_threshold=2),
        
        # File upload endpoints (resource intensive)
        "/transcribe": SecurityRateLimit(3, 3600, ban_threshold=10),  # 3 uploads per hour
        "/upload": SecurityRateLimit(5, 3600, ban_threshold=15),
        "/chunked-upload": SecurityRateLimit(10, 3600, ban_threshold=20),
        
        # API endpoints
        "/jobs": SecurityRateLimit(60, 60),
        "/jobs/*": SecurityRateLimit(30, 60),
        "/api/*": SecurityRateLimit(100, 60),
        
        # Health and monitoring
        "/health": SecurityRateLimit(60, 60),
        "/metrics": SecurityRateLimit(20, 60),
    },
    
    # Security settings
    enable_ip_blacklist=True,
    enable_threat_detection=True,
    enable_progressive_delays=True,
    enable_security_logging=True,
    
    # Performance settings
    cleanup_interval=300,
    max_memory_entries=50000
)

# Development configuration (more lenient)
DEVELOPMENT_CONFIG = EnhancedRateLimitConfig(
    global_limit=SecurityRateLimit(120, 60, ban_threshold=30),  # More lenient for dev
    user_limit=SecurityRateLimit(1000, 3600),
    
    endpoint_limits={
        "/token": SecurityRateLimit(10, 60, ban_threshold=15),
        "/login": SecurityRateLimit(10, 60, ban_threshold=15),
        "/register": SecurityRateLimit(5, 3600, ban_threshold=10),
        "/transcribe": SecurityRateLimit(10, 3600, ban_threshold=20),
        "/upload": SecurityRateLimit(20, 3600, ban_threshold=30),
        "/admin/*": SecurityRateLimit(60, 60, ban_threshold=20),
        "/jobs": SecurityRateLimit(120, 60),
        "/health": SecurityRateLimit(240, 60),
    },
    
    enable_threat_detection=True,
    enable_progressive_delays=False,  # Disable delays in dev
    enable_security_logging=True
)

# Test configuration (very lenient)
TEST_CONFIG = EnhancedRateLimitConfig(
    global_limit=SecurityRateLimit(1000, 60),  # Very high limits for testing
    user_limit=SecurityRateLimit(5000, 3600),
    
    endpoint_limits={
        "/token": SecurityRateLimit(100, 60),
        "/transcribe": SecurityRateLimit(100, 3600),
        "/admin/*": SecurityRateLimit(200, 60),
    },
    
    enable_threat_detection=False,  # Disable for testing
    enable_progressive_delays=False,
    enable_security_logging=False
)
