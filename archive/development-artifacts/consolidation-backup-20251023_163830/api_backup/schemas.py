"""
Base schema definitions for the API.
Provides common response structures and validation models.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response structure for API endpoints."""
    success: bool = True
    message: str = "Operation completed successfully"
    timestamp: datetime = datetime.utcnow()
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseResponse):
    """Error response structure."""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseResponse):
    """Success response structure."""
    success: bool = True