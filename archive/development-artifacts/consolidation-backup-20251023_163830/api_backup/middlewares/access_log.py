"""
Access logging middleware for the Whisper Transcriber API.
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from api.utils.logger import get_system_logger

# Create a dedicated access logger
access_logger = get_system_logger("access")

class AccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP access requests."""
    
    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()
        
        # Get client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log access information
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_time)),
            "client_ip": client_ip,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": response.status_code,
            "response_time_ms": round(process_time * 1000, 2),
            "user_agent": user_agent,
            "content_length": response.headers.get("content-length", "0")
        }
        
        # Add authentication info if available
        if "authorization" in request.headers:
            log_data["authenticated"] = True
        
        # Log the access
        if response.status_code >= 400:
            access_logger.warning(json.dumps(log_data))
        else:
            access_logger.info(json.dumps(log_data))
        
        # Add response time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
