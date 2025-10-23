"""
Enhanced Pydantic schemas with comprehensive input validation for security.

This module provides type-safe, validated schemas for all API endpoints with
security-focused validation to prevent common attack vectors:
- SQL injection prevention
- XSS protection  
- Input sanitization
- Data type validation
- Field length limits
- Pattern validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, field_validator
from pydantic_core import ValidationError
import re
import html
import bleach


# Configuration for input validation
class ValidationConfig:
    """Security-focused validation configuration."""
    
    # String length limits
    MAX_FILENAME_LENGTH = 255
    MAX_USERNAME_LENGTH = 50
    MAX_PASSWORD_LENGTH = 128
    MIN_PASSWORD_LENGTH = 8
    MAX_JOB_ID_LENGTH = 36
    MAX_ERROR_MESSAGE_LENGTH = 1000
    MAX_MODEL_NAME_LENGTH = 50
    
    # Pattern validation
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+\.[a-zA-Z0-9]{1,10}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    JOB_ID_PATTERN = re.compile(r'^[a-fA-F0-9-]+$')
    
    # Dangerous patterns to reject
    DANGEROUS_PATTERNS = [
        # SQL injection patterns - more specific
        r"('|(\\x27)|(\\x2D))",
        r"(;|\s)(\s)*(select|insert|update|delete|drop|create|alter|exec|execute)\s",
        r"(\s)(union|having)\s+",
        r"order\s+by\s+[^a-zA-Z_]",  # Allow legitimate ORDER BY field names
        
        # XSS patterns  
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        
        # Path traversal
        r"\.\.[\\/]",
        r"[\\/]etc[\\/]",
        r"[\\/]proc[\\/]",
        
        # Command injection - exclude underscore from dangerous chars
        r"[;&|`$(){}[\]\\]",
    ]


def sanitize_string(value: str, allow_html: bool = False) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks.
    
    Args:
        value: Input string to sanitize
        allow_html: If True, allows safe HTML tags
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")
    
    # Remove null bytes and control characters
    value = value.replace('\x00', '').replace('\r', '').replace('\n', ' ')
    
    # Limit length to prevent DoS
    if len(value) > 10000:
        raise ValueError("Input string too long")
    
    # HTML escape unless specifically allowing HTML
    if not allow_html:
        value = html.escape(value, quote=True)
    else:
        # Use bleach for safe HTML sanitization
        allowed_tags = ['b', 'i', 'u', 'em', 'strong']
        value = bleach.clean(value, tags=allowed_tags, strip=True)
    
    # Check for dangerous patterns
    for pattern in ValidationConfig.DANGEROUS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f"Input contains potentially dangerous content")
    
    return value.strip()


def validate_no_sql_injection(value: str) -> str:
    """Validate that string doesn't contain SQL injection patterns."""
    dangerous_sql = [
        'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter',
        'union', 'script', 'exec', 'execute', '--', '/*', '*/', ';'
    ]
    
    value_lower = value.lower()
    for pattern in dangerous_sql:
        if pattern in value_lower:
            raise ValueError(f"Input contains potentially dangerous SQL pattern: {pattern}")
    
    return value


# Base schema with common validation
class BaseSchema(BaseModel):
    """Base schema with security validation."""
    
    class Config:
        # Validate assignment to prevent mutation attacks
        validate_assignment = True
        # Use enum values to prevent injection
        use_enum_values = True
        # Validate default values
        validate_default = True
        # Forbid extra fields to prevent parameter pollution
        extra = 'forbid'


# Authentication schemas
class UserRegistrationSchema(BaseSchema):
    """Secure user registration with validation."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=ValidationConfig.MAX_USERNAME_LENGTH,
        description="Username (3-50 characters, alphanumeric, dash, underscore only)"
    )
    password: str = Field(
        ...,
        min_length=ValidationConfig.MIN_PASSWORD_LENGTH,
        max_length=ValidationConfig.MAX_PASSWORD_LENGTH,
        description="Password (8-128 characters)"
    )
    is_admin: Optional[bool] = Field(
        default=False,
        description="Admin privileges (default: false)"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format and security."""
        v = sanitize_string(v)
        
        if not ValidationConfig.USERNAME_PATTERN.match(v):
            raise ValueError("Username must contain only letters, numbers, hyphens, and underscores")
        
        # Prevent reserved usernames
        reserved = ['admin', 'root', 'system', 'api', 'test', 'guest', 'anonymous']
        if v.lower() in reserved:
            raise ValueError("Username is reserved")
        
        return validate_no_sql_injection(v)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength and security."""
        if len(v) < ValidationConfig.MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {ValidationConfig.MIN_PASSWORD_LENGTH} characters")
        
        # Check for common patterns that indicate weak passwords
        if v.lower() in ['password', '12345678', 'qwerty123', 'admin123']:
            raise ValueError("Password is too common")
        
        # Ensure some complexity (at least one letter and one number)
        if not re.search(r'[a-zA-Z]', v) or not re.search(r'\d', v):
            raise ValueError("Password must contain both letters and numbers")
        
        return v


class UserLoginSchema(BaseSchema):
    """Secure user login with validation."""
    
    username: str = Field(
        ...,
        max_length=ValidationConfig.MAX_USERNAME_LENGTH,
        description="Username"
    )
    password: str = Field(
        ...,
        max_length=ValidationConfig.MAX_PASSWORD_LENGTH,
        description="Password"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return validate_no_sql_injection(sanitize_string(v))
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Don't sanitize passwords (they may contain special chars)
        # But check length to prevent DoS
        if len(v) > ValidationConfig.MAX_PASSWORD_LENGTH:
            raise ValueError("Password too long")
        return v


class PasswordChangeSchema(BaseSchema):
    """Secure password change with validation."""
    
    current_password: str = Field(
        ...,
        max_length=ValidationConfig.MAX_PASSWORD_LENGTH,
        description="Current password"
    )
    new_password: str = Field(
        ...,
        min_length=ValidationConfig.MIN_PASSWORD_LENGTH,
        max_length=ValidationConfig.MAX_PASSWORD_LENGTH,
        description="New password (8-128 characters)"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Apply same validation as registration."""
        return UserRegistrationSchema.validate_password(v)


# File upload schemas  
class FileUploadSchema(BaseSchema):
    """Secure file upload validation."""
    
    filename: Optional[str] = Field(
        None,
        max_length=ValidationConfig.MAX_FILENAME_LENGTH,
        description="Original filename"
    )
    model: Optional[str] = Field(
        default="small",
        max_length=ValidationConfig.MAX_MODEL_NAME_LENGTH,
        description="Whisper model to use"
    )
    language: Optional[str] = Field(
        None,
        max_length=10,
        description="Language code (e.g., 'en', 'es')"
    )
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: Optional[str]) -> Optional[str]:
        """Validate filename security."""
        if v is None:
            return v
            
        v = sanitize_string(v)
        
        # Check filename pattern
        if not ValidationConfig.FILENAME_PATTERN.match(v):
            raise ValueError("Invalid filename format")
        
        # Prevent path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Filename cannot contain path separators")
        
        return validate_no_sql_injection(v)
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: Optional[str]) -> Optional[str]:
        """Validate model name."""
        if v is None:
            return v
            
        v = sanitize_string(v)
        
        # Allowlist of valid models
        valid_models = ['tiny', 'small', 'medium', 'large', 'large-v2', 'large-v3']
        if v not in valid_models:
            raise ValueError(f"Invalid model. Must be one of: {', '.join(valid_models)}")
        
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate language code."""
        if v is None:
            return v
            
        v = sanitize_string(v)
        
        # Basic language code validation (ISO 639-1)
        if not re.match(r'^[a-z]{2}$', v.lower()):
            raise ValueError("Language must be a 2-letter ISO code (e.g., 'en', 'es')")
        
        return v.lower()


# Job management schemas
class JobQuerySchema(BaseSchema):
    """Secure job query parameters."""
    
    limit: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of jobs to return (1-100)"
    )
    offset: Optional[int] = Field(
        default=0,
        ge=0,
        le=10000,
        description="Number of jobs to skip (0-10000)"
    )
    status: Optional[str] = Field(
        None,
        max_length=20,
        description="Filter by job status"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate job status."""
        if v is None:
            return v
            
        v = sanitize_string(v)
        
        # Allowlist of valid statuses
        valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        return v


class JobIdSchema(BaseSchema):
    """Secure job ID validation."""
    
    job_id: str = Field(
        ...,
        min_length=1,
        max_length=ValidationConfig.MAX_JOB_ID_LENGTH,
        description="Job identifier"
    )
    
    @field_validator('job_id')
    @classmethod
    def validate_job_id(cls, v: str) -> str:
        """Validate job ID format."""
        v = sanitize_string(v)
        
        if not ValidationConfig.JOB_ID_PATTERN.match(v):
            raise ValueError("Invalid job ID format")
        
        return validate_no_sql_injection(v)


# Response schemas with sanitization
class TokenResponseSchema(BaseSchema):
    """Secure token response."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")


class UserResponseSchema(BaseSchema):
    """Secure user information response."""
    
    username: str = Field(..., description="Username")
    is_admin: bool = Field(..., description="Admin privileges")
    created_at: datetime = Field(..., description="Account creation date")
    must_change_password: bool = Field(default=False, description="Password change required")
    
    @field_validator('username')
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Ensure username is sanitized in responses."""
        return sanitize_string(v)


class JobResponseSchema(BaseSchema):
    """Secure job information response."""
    
    id: str = Field(..., description="Job identifier")
    filename: str = Field(..., description="Original filename") 
    status: str = Field(..., description="Job status")
    model_used: Optional[str] = Field(None, description="Whisper model used")
    created_at: datetime = Field(..., description="Job creation date")
    completed_at: Optional[datetime] = Field(None, description="Job completion date")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    duration: Optional[int] = Field(None, description="Audio duration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @field_validator('filename', 'error_message')
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields in responses."""
        if v is None:
            return v
        return sanitize_string(v)


class PaginatedJobsResponseSchema(BaseSchema):
    """Paginated job listing response."""
    
    data: List[JobResponseSchema] = Field(..., description="Job data")
    pagination: dict = Field(..., description="Pagination metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "filename": "audio.mp3",
                        "status": "completed",
                        "model_used": "small",
                        "created_at": "2025-10-15T10:00:00Z",
                        "completed_at": "2025-10-15T10:05:00Z",
                        "file_size": 1024000,
                        "duration": 300,
                        "error_message": None
                    }
                ],
                "pagination": {
                    "page_size": 20,
                    "total_count": 100,
                    "has_next": True,
                    "has_previous": False,
                    "next_cursor": "eyJpZCI6IjEyMyIsInNvcnRfdmFsdWUiOiIyMDI1LTEwLTE1VDEwOjAwOjAwWiJ9",
                    "previous_cursor": None,
                    "sort_by": "created_at",
                    "sort_order": "desc"
                }
            }
        }


class ErrorResponseSchema(BaseSchema):
    """Secure error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    @field_validator('message')
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """Sanitize error message."""
        return sanitize_string(v)


# Health and monitoring schemas
class HealthResponseSchema(BaseSchema):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version") 
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")


class MetricsResponseSchema(BaseSchema):
    """Metrics response schema."""
    
    total_jobs: int = Field(..., description="Total number of jobs")
    pending_jobs: int = Field(..., description="Number of pending jobs")
    processing_jobs: int = Field(..., description="Number of processing jobs")
    completed_jobs: int = Field(..., description="Number of completed jobs")
    failed_jobs: int = Field(..., description="Number of failed jobs")
    system_load: float = Field(..., description="System load average")
    memory_usage: float = Field(..., description="Memory usage percentage")


# Validation utilities
def validate_request_size(content_length: Optional[int], max_size: int = 104857600) -> None:
    """Validate request size to prevent DoS attacks."""
    if content_length and content_length > max_size:
        raise ValueError(f"Request too large. Maximum size: {max_size // 1024 // 1024}MB")


def validate_json_depth(data: Any, max_depth: int = 10, current_depth: int = 0) -> None:
    """Validate JSON depth to prevent nested object DoS attacks."""
    if current_depth > max_depth:
        raise ValueError("JSON structure too deeply nested")
    
    if isinstance(data, dict):
        for value in data.values():
            validate_json_depth(value, max_depth, current_depth + 1)
    elif isinstance(data, list):
        for item in data:
            validate_json_depth(item, max_depth, current_depth + 1)


def create_validation_error_response(error: ValidationError) -> Dict[str, Any]:
    """Create a sanitized validation error response."""
    return {
        "error": "validation_error",
        "message": "Input validation failed",
        "details": {
            "field_errors": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": sanitize_string(str(err["msg"])),
                    "type": err["type"]
                }
                for err in error.errors()
            ]
        }
    }
