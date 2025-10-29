#!/usr/bin/env python3
"""
T027 Advanced Features: API Key Authentication Middleware
FastAPI middleware for API key authentication and rate limiting.
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.services.api_key_service import api_key_service
from api.extended_models.api_keys import APIKey, APIKeyPermission
from api.utils.logger import get_system_logger

logger = get_system_logger("api_key_middleware")

class APIKeyAuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication and validation."""
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico",
            "/auth/login",
            "/auth/register",
            "/auth/token",
            "/api/auth/login",
            "/api/auth/register", 
            "/api/auth/token",
            "/login",
            "/register",
            "/token",
            "/jobs/"  # TEMPORARY: bypass auth for testing job model
        }
        
        # Rate limiting storage (in production, use Redis)
        self.rate_limit_storage = {}
        self.quota_storage = {}
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Skip authentication for exempt paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # Extract API key from request
        api_key = self._extract_api_key(request)
        
        if not api_key:
            # No API key provided - check if endpoint requires authentication
            if self._requires_authentication(request.url.path):
                return self._create_auth_error_response("API key required")
            return await call_next(request)
        
        # Get database session
        db = next(get_db())
        
        try:
            # Validate API key
            client_ip = self._get_client_ip(request)
            required_permission = self._get_required_permission(request.url.path, request.method)
            
            db_api_key = api_key_service.validate_api_key(
                db, api_key, required_permission, client_ip
            )
            
            if not db_api_key:
                return self._create_auth_error_response("Invalid or expired API key")
            
            # Check rate limits
            rate_limit_result = self._check_rate_limits(db_api_key, client_ip)
            if not rate_limit_result["allowed"]:
                return self._create_rate_limit_error_response(rate_limit_result)
            
            # Check quotas
            quota_result = self._check_quotas(db, db_api_key)
            if not quota_result["allowed"]:
                return self._create_quota_error_response(quota_result)
            
            # Add API key info to request state
            request.state.api_key = db_api_key
            request.state.user_id = db_api_key.user_id
            request.state.api_permissions = db_api_key.permissions_list
            
            # Process the request
            response = await call_next(request)
            
            # Log the API key usage
            processing_time = int((time.time() - start_time) * 1000)
            self._log_api_key_usage(
                db, db_api_key, request, response, client_ip, processing_time
            )
            
            # Add rate limit headers to response
            self._add_rate_limit_headers(response, rate_limit_result)
            
            return response
            
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return self._create_auth_error_response("Authentication error")
        
        finally:
            db.close()
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from API key authentication."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)
    
    def _requires_authentication(self, path: str) -> bool:
        """Check if path requires authentication."""
        # Skip authentication for auth endpoints
        auth_patterns = ["/auth/", "/login", "/register", "/token"]
        if any(path.startswith(pattern) or pattern in path for pattern in auth_patterns):
            return False
            
        # API paths that require authentication  
        protected_prefixes = ["/api/transcribe", "/api/jobs", "/admin/", "/upload/"]
        return any(path.startswith(prefix) for prefix in protected_prefixes)
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers."""
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Check Authorization header with "Bearer" scheme
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, credentials = get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer" and credentials.startswith("wt_"):
                return credentials
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _get_required_permission(self, path: str, method: str) -> Optional[str]:
        """Determine required permission for the endpoint."""
        # Admin endpoints require admin permission
        if path.startswith("/admin/"):
            return APIKeyPermission.ADMIN.value
        
        # Batch endpoints require batch permission
        if "/batch" in path:
            return APIKeyPermission.BATCH.value
        
        # Write operations require write permission
        if method in ["POST", "PUT", "PATCH"]:
            return APIKeyPermission.WRITE.value
        
        # Delete operations require delete permission
        if method == "DELETE":
            return APIKeyPermission.DELETE.value
        
        # Read operations require read permission
        return APIKeyPermission.READ.value
    
    def _check_rate_limits(self, api_key: APIKey, client_ip: str) -> Dict[str, Any]:
        """Check rate limits for the API key."""
        current_time = datetime.utcnow()
        rate_limit = api_key.rate_limit_per_hour or 1000
        
        # Create rate limit key
        rate_key = f"{api_key.key_id}:{client_ip}"
        
        # Get current window (1 hour)
        window_start = current_time.replace(minute=0, second=0, microsecond=0)
        
        # Get or create rate limit record
        if rate_key not in self.rate_limit_storage:
            self.rate_limit_storage[rate_key] = {
                "window_start": window_start,
                "count": 0,
                "blocked_until": None
            }
        
        record = self.rate_limit_storage[rate_key]
        
        # Reset if new window
        if record["window_start"] < window_start:
            record["window_start"] = window_start
            record["count"] = 0
            record["blocked_until"] = None
        
        # Check if currently blocked
        if record["blocked_until"] and current_time < record["blocked_until"]:
            return {
                "allowed": False,
                "limit": rate_limit,
                "remaining": 0,
                "reset_time": record["blocked_until"],
                "retry_after": int((record["blocked_until"] - current_time).total_seconds())
            }
        
        # Check if over limit
        if record["count"] >= rate_limit:
            # Block for 15 minutes
            record["blocked_until"] = current_time + timedelta(minutes=15)
            return {
                "allowed": False,
                "limit": rate_limit,
                "remaining": 0,
                "reset_time": window_start + timedelta(hours=1),
                "retry_after": 900  # 15 minutes
            }
        
        # Allow the request
        record["count"] += 1
        
        return {
            "allowed": True,
            "limit": rate_limit,
            "remaining": rate_limit - record["count"],
            "reset_time": window_start + timedelta(hours=1)
        }
    
    def _check_quotas(self, db: Session, api_key: APIKey) -> Dict[str, Any]:
        """Check daily/monthly quotas for the API key."""
        current_time = datetime.utcnow()
        
        # Check daily quota
        if api_key.daily_quota:
            daily_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_usage = self._get_usage_count(db, api_key.id, daily_start, current_time)
            
            if daily_usage >= api_key.daily_quota:
                return {
                    "allowed": False,
                    "quota_type": "daily",
                    "limit": api_key.daily_quota,
                    "used": daily_usage,
                    "reset_time": daily_start + timedelta(days=1)
                }
        
        # Check monthly quota
        if api_key.monthly_quota:
            monthly_start = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_usage = self._get_usage_count(db, api_key.id, monthly_start, current_time)
            
            if monthly_usage >= api_key.monthly_quota:
                # Calculate next month
                if monthly_start.month == 12:
                    next_month = monthly_start.replace(year=monthly_start.year + 1, month=1)
                else:
                    next_month = monthly_start.replace(month=monthly_start.month + 1)
                
                return {
                    "allowed": False,
                    "quota_type": "monthly",
                    "limit": api_key.monthly_quota,
                    "used": monthly_usage,
                    "reset_time": next_month
                }
        
        return {"allowed": True}
    
    def _get_usage_count(self, db: Session, api_key_id: int, start_time: datetime, end_time: datetime) -> int:
        """Get usage count for a time period."""
        from api.extended_models.api_keys import APIKeyUsageLog
        
        count = db.query(APIKeyUsageLog).filter(
            APIKeyUsageLog.api_key_id == api_key_id,
            APIKeyUsageLog.timestamp >= start_time,
            APIKeyUsageLog.timestamp < end_time
        ).count()
        
        return count
    
    def _log_api_key_usage(
        self,
        db: Session,
        api_key: APIKey,
        request: Request,
        response: Response,
        client_ip: str,
        processing_time: int
    ):
        """Log API key usage."""
        try:
            api_key_service.log_api_key_usage(
                db=db,
                api_key=api_key,
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                client_ip=client_ip,
                user_agent=request.headers.get("User-Agent"),
                response_time_ms=processing_time,
                request_size_bytes=int(request.headers.get("Content-Length", 0)),
                response_size_bytes=len(response.body) if hasattr(response, "body") else None
            )
        except Exception as e:
            logger.error(f"Failed to log API key usage: {e}")
    
    def _add_rate_limit_headers(self, response: Response, rate_limit_result: Dict[str, Any]):
        """Add rate limit headers to response."""
        if "limit" in rate_limit_result:
            response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        if "remaining" in rate_limit_result:
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        if "reset_time" in rate_limit_result:
            response.headers["X-RateLimit-Reset"] = str(int(rate_limit_result["reset_time"].timestamp()))
    
    def _create_auth_error_response(self, message: str) -> Response:
        """Create authentication error response."""
        return Response(
            content=f'{{"detail": "{message}", "error_code": "AUTHENTICATION_REQUIRED"}}',
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"Content-Type": "application/json"}
        )
    
    def _create_rate_limit_error_response(self, rate_limit_result: Dict[str, Any]) -> Response:
        """Create rate limit error response."""
        headers = {
            "Content-Type": "application/json",
            "X-RateLimit-Limit": str(rate_limit_result["limit"]),
            "X-RateLimit-Remaining": "0"
        }
        
        if "retry_after" in rate_limit_result:
            headers["Retry-After"] = str(rate_limit_result["retry_after"])
        
        return Response(
            content=f'{{"detail": "Rate limit exceeded", "error_code": "RATE_LIMIT_EXCEEDED", "retry_after": {rate_limit_result.get("retry_after", 0)}}}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers
        )
    
    def _create_quota_error_response(self, quota_result: Dict[str, Any]) -> Response:
        """Create quota exceeded error response."""
        return Response(
            content=f'{{"detail": "Quota exceeded", "error_code": "QUOTA_EXCEEDED", "quota_type": "{quota_result.get("quota_type", "unknown")}"}}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Content-Type": "application/json"}
        )