#!/usr/bin/env python3
"""
T026 Security Hardening: Rate Limiting Integration Script
Integrates enhanced rate limiting into the whisper-transcriber application.
"""

import os
import shutil
from pathlib import Path

def integrate_enhanced_rate_limiter():
    """Integrate the enhanced rate limiter into the application."""
    project_root = Path("/home/buymeagoat/dev/whisper-transcriber")
    
    print("🚦 T026 Security Hardening: Integrating Enhanced Rate Limiting")
    print("=" * 70)
    
    # Copy enhanced rate limiter to the api/middlewares directory
    source_file = project_root / "temp" / "enhanced_rate_limiter.py"
    target_file = project_root / "api" / "middlewares" / "enhanced_rate_limiter.py"
    
    # Create middlewares directory if it doesn't exist
    target_file.parent.mkdir(exist_ok=True)
    
    # Copy the file
    shutil.copy2(source_file, target_file)
    print(f"✅ Copied enhanced rate limiter to {target_file}")
    
    # Create configuration file
    config_content = '''"""
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
'''
    
    config_file = project_root / "api" / "middlewares" / "rate_limit_config.py"
    with open(config_file, 'w') as f:
        f.write(config_content)
    print(f"✅ Created rate limiting configuration at {config_file}")
    
    # Create integration helper
    integration_content = '''"""
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
'''
    
    integration_file = project_root / "api" / "middlewares" / "rate_limit_integration.py"
    with open(integration_file, 'w') as f:
        f.write(integration_content)
    print(f"✅ Created rate limiting integration helper at {integration_file}")
    
    # Update main application to use enhanced rate limiting
    main_py_path = project_root / "api" / "main.py"
    
    if main_py_path.exists():
        # Read current main.py
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Check if rate limiting is already integrated
        if "EnhancedRateLimitMiddleware" not in content:
            # Add import at the top
            import_line = "from api.middlewares.rate_limit_integration import add_rate_limiting\\n"
            
            # Find a good place to add the import
            lines = content.split('\\n')
            import_added = False
            
            for i, line in enumerate(lines):
                if line.startswith('from api.') and not import_added:
                    lines.insert(i + 1, import_line.strip())
                    import_added = True
                    break
            
            if not import_added:
                # Add after other imports
                for i, line in enumerate(lines):
                    if line.strip() == '' and i > 0:
                        lines.insert(i, import_line.strip())
                        break
            
            # Find where to add rate limiting initialization
            app_creation_found = False
            for i, line in enumerate(lines):
                if 'app = FastAPI(' in line or 'app=FastAPI(' in line:
                    # Add rate limiting after app creation
                    j = i + 1
                    while j < len(lines) and lines[j].strip().endswith((',', ')')):
                        j += 1
                    
                    # Add rate limiting configuration
                    env_detection = '''
# Detect environment for rate limiting
import os
environment = os.getenv("ENVIRONMENT", "production")
if environment not in ["production", "development", "test"]:
    environment = "production"  # Default to production for security

# Add enhanced rate limiting
add_rate_limiting(app, environment)'''
                    
                    lines.insert(j + 1, env_detection)
                    app_creation_found = True
                    break
            
            if app_creation_found:
                # Write updated content
                with open(main_py_path, 'w') as f:
                    f.write('\\n'.join(lines))
                print(f"✅ Integrated enhanced rate limiting into {main_py_path}")
            else:
                print(f"⚠️  Could not automatically integrate into {main_py_path}")
                print("   Please manually add rate limiting using:")
                print("   from api.middlewares.rate_limit_integration import add_rate_limiting")
                print("   add_rate_limiting(app, 'production')")
        else:
            print(f"✅ Enhanced rate limiting already integrated in {main_py_path}")
    
    # Create Redis dependency note
    redis_note = '''# Enhanced Rate Limiting Redis Support
#
# For production deployments, consider using Redis for distributed rate limiting:
#
# 1. Install Redis: sudo apt install redis-server
# 2. Install Python Redis client: pip install redis>=4.0.0
# 3. Update rate_limit_config.py to enable Redis:
#    use_redis=True,
#    redis_url="redis://localhost:6379/1"
#
# Benefits of Redis:
# - Shared rate limiting across multiple application instances
# - Persistent rate limit data across application restarts
# - Better performance for high-traffic applications
# - Distributed denial-of-service protection
'''
    
    redis_file = project_root / "api" / "middlewares" / "redis_setup.md"
    with open(redis_file, 'w') as f:
        f.write(redis_note)
    print(f"✅ Created Redis setup guide at {redis_file}")
    
    print("\\n" + "=" * 70)
    print("🚦 ENHANCED RATE LIMITING INTEGRATION COMPLETE")
    print("=" * 70)
    print("Features added:")
    print("  • IP-based rate limiting with auto-banning")
    print("  • User-based rate limiting for authenticated requests")
    print("  • Endpoint-specific limits with security focus")
    print("  • Threat detection and progressive delays")
    print("  • Comprehensive security logging")
    print("  • Environment-specific configurations")
    print("\\nNext steps:")
    print("  • Review rate limit configurations in api/middlewares/rate_limit_config.py")
    print("  • Consider Redis integration for production (see redis_setup.md)")
    print("  • Monitor security logs in logs/security_events.log")
    print("  • Test rate limiting with your application endpoints")

if __name__ == "__main__":
    integrate_enhanced_rate_limiter()