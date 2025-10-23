# Enhanced Rate Limiting Redis Support
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
