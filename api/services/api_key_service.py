#!/usr/bin/env python3
"""
T027 Advanced Features: API Key Management Service
Core service for managing developer API keys with comprehensive functionality.
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import uuid
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from api.models.api_keys import APIKey, APIKeyUsageLog, APIKeyQuotaUsage, APIKeyStatus, APIKeyPermission
from api.utils.logger import get_system_logger

logger = get_system_logger("api_key_service")

class APIKeyCreateRequest(BaseModel):
    """Request model for creating API keys."""
    name: str = Field(..., min_length=1, max_length=255, description="User-friendly name for the API key")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    permissions: List[str] = Field(..., min_items=1, description="List of permissions for the API key")
    expires_days: Optional[int] = Field(None, ge=1, le=3650, description="Expiration in days (1-3650)")
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=10000, description="Rate limit per hour")
    daily_quota: Optional[int] = Field(None, ge=1, description="Daily request quota")
    monthly_quota: Optional[int] = Field(None, ge=1, description="Monthly request quota")
    allowed_ips: Optional[List[str]] = Field(None, description="List of allowed IP addresses/ranges")

class APIKeyResponse(BaseModel):
    """Response model for API key information."""
    key_id: str
    name: str
    description: Optional[str]
    permissions: List[str]
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    last_used_ip: Optional[str]
    rate_limit_per_hour: Optional[int]
    daily_quota: Optional[int]
    monthly_quota: Optional[int]
    allowed_ips: Optional[List[str]]
    is_active: bool

class APIKeyWithSecret(BaseModel):
    """Response model for newly created API key with secret."""
    key_id: str
    api_key: str  # The actual secret key - only shown once
    name: str
    description: Optional[str]
    permissions: List[str]
    expires_at: Optional[datetime]
    rate_limit_per_hour: Optional[int]
    daily_quota: Optional[int]
    monthly_quota: Optional[int]

class APIKeyUsageStats(BaseModel):
    """API key usage statistics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    rate_limited_requests: int
    quota_exceeded_requests: int
    average_response_time_ms: float
    total_bytes_uploaded: int
    total_bytes_downloaded: int
    last_24h_requests: int
    last_7d_requests: int
    top_endpoints: List[Dict[str, Any]]

class APIKeyManagementService:
    """Comprehensive API key management service."""
    
    def __init__(self):
        self.key_prefix = "wt_"  # Whisper Transcriber prefix
        self.key_length = 32  # Length of the secret part
        self.default_rate_limit = 1000  # Default requests per hour
        self.default_expiry_days = 365  # Default expiration
        
    def generate_api_key(self) -> Tuple[str, str, str]:
        """
        Generate a new API key.
        
        Returns:
            Tuple of (key_id, full_api_key, key_hash)
        """
        # Generate unique key ID
        key_id = str(uuid.uuid4())
        
        # Generate random secret
        secret = secrets.token_urlsafe(self.key_length)
        
        # Create full API key with prefix
        full_key = f"{self.key_prefix}{secret}"
        
        # Create hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        return key_id, full_key, key_hash
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def validate_permissions(self, permissions: List[str]) -> bool:
        """Validate that all permissions are valid."""
        valid_permissions = {perm.value for perm in APIKeyPermission}
        return all(perm in valid_permissions for perm in permissions)
    
    def create_api_key(
        self,
        db: Session,
        user_id: str,
        request: APIKeyCreateRequest
    ) -> APIKeyWithSecret:
        """Create a new API key."""
        
        # Validate permissions
        if not self.validate_permissions(request.permissions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid permissions specified"
            )
        
        # Check if user already has a key with this name
        existing_key = db.query(APIKey).filter(
            and_(
                APIKey.user_id == user_id,
                APIKey.name == request.name,
                APIKey.status != APIKeyStatus.REVOKED.value
            )
        ).first()
        
        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key with this name already exists"
            )
        
        # Generate API key
        key_id, full_key, key_hash = self.generate_api_key()
        
        # Calculate expiration
        expires_at = None
        if request.expires_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_days)
        elif self.default_expiry_days:
            expires_at = datetime.utcnow() + timedelta(days=self.default_expiry_days)
        
        # Create database record
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            key_prefix=full_key[:12],  # Store first 12 chars for identification
            name=request.name,
            description=request.description,
            user_id=user_id,
            permissions=request.permissions,
            status=APIKeyStatus.ACTIVE.value,
            expires_at=expires_at,
            rate_limit_per_hour=request.rate_limit_per_hour or self.default_rate_limit,
            daily_quota=request.daily_quota,
            monthly_quota=request.monthly_quota,
            allowed_ips=request.allowed_ips
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        logger.info(f"Created API key '{request.name}' for user {user_id}")
        
        return APIKeyWithSecret(
            key_id=key_id,
            api_key=full_key,
            name=request.name,
            description=request.description,
            permissions=request.permissions,
            expires_at=expires_at,
            rate_limit_per_hour=api_key.rate_limit_per_hour,
            daily_quota=request.daily_quota,
            monthly_quota=request.monthly_quota
        )
    
    def validate_api_key(
        self,
        db: Session,
        api_key: str,
        required_permission: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> Optional[APIKey]:
        """
        Validate an API key and check permissions.
        
        Returns:
            APIKey object if valid, None if invalid
        """
        if not api_key or not api_key.startswith(self.key_prefix):
            return None
        
        # Hash the provided key
        key_hash = self.hash_api_key(api_key)
        
        # Find the key in database
        db_key = db.query(APIKey).filter(
            and_(
                APIKey.key_hash == key_hash,
                APIKey.status == APIKeyStatus.ACTIVE.value
            )
        ).first()
        
        if not db_key:
            return None
        
        # Check expiration
        if db_key.expires_at and db_key.expires_at < datetime.utcnow():
            # Auto-expire the key
            db_key.status = APIKeyStatus.EXPIRED.value
            db.commit()
            return None
        
        # Check IP restrictions
        if db_key.allowed_ips and client_ip:
            if not self._is_ip_allowed(client_ip, db_key.allowed_ips):
                logger.warning(f"API key {db_key.key_id} used from unauthorized IP: {client_ip}")
                return None
        
        # Check required permission
        if required_permission and not db_key.has_permission(required_permission):
            return None
        
        return db_key
    
    def _is_ip_allowed(self, client_ip: str, allowed_ips: List[str]) -> bool:
        """Check if client IP is in allowed list."""
        # Simple implementation - could be enhanced with CIDR support
        return client_ip in allowed_ips
    
    def log_api_key_usage(
        self,
        db: Session,
        api_key: APIKey,
        method: str,
        endpoint: str,
        status_code: int,
        client_ip: str,
        user_agent: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None,
        rate_limited: bool = False,
        quota_exceeded: bool = False
    ):
        """Log API key usage."""
        
        # Update API key usage statistics
        api_key.update_usage(client_ip, user_agent)
        
        # Create usage log entry
        usage_log = APIKeyUsageLog(
            api_key_id=api_key.id,
            timestamp=datetime.utcnow(),
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time_ms,
            client_ip=client_ip,
            user_agent=user_agent,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            error_message=error_message,
            rate_limited=rate_limited,
            quota_exceeded=quota_exceeded
        )
        
        db.add(usage_log)
        db.commit()
    
    def get_user_api_keys(self, db: Session, user_id: str) -> List[APIKeyResponse]:
        """Get all API keys for a user."""
        keys = db.query(APIKey).filter(
            APIKey.user_id == user_id
        ).order_by(desc(APIKey.created_at)).all()
        
        return [
            APIKeyResponse(
                key_id=key.key_id,
                name=key.name,
                description=key.description,
                permissions=key.permissions_list,
                status=key.status,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                last_used_ip=key.last_used_ip,
                rate_limit_per_hour=key.rate_limit_per_hour,
                daily_quota=key.daily_quota,
                monthly_quota=key.monthly_quota,
                allowed_ips=key.allowed_ips,
                is_active=key.is_active
            )
            for key in keys
        ]
    
    def revoke_api_key(
        self,
        db: Session,
        user_id: str,
        key_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Revoke an API key."""
        api_key = db.query(APIKey).filter(
            and_(
                APIKey.key_id == key_id,
                APIKey.user_id == user_id,
                APIKey.status != APIKeyStatus.REVOKED.value
            )
        ).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        api_key.status = APIKeyStatus.REVOKED.value
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = user_id
        api_key.revoked_reason = reason
        
        db.commit()
        
        logger.info(f"Revoked API key {key_id} for user {user_id}. Reason: {reason}")
        return True
    
    def get_api_key_usage_stats(
        self,
        db: Session,
        api_key_id: str,
        days: int = 30
    ) -> APIKeyUsageStats:
        """Get usage statistics for an API key."""
        
        # Find the API key
        api_key = db.query(APIKey).filter(APIKey.key_id == api_key_id).first()
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get usage logs
        usage_logs = db.query(APIKeyUsageLog).filter(
            and_(
                APIKeyUsageLog.api_key_id == api_key.id,
                APIKeyUsageLog.timestamp >= start_date
            )
        ).all()
        
        # Calculate statistics
        total_requests = len(usage_logs)
        successful_requests = len([log for log in usage_logs if 200 <= log.status_code < 400])
        failed_requests = total_requests - successful_requests
        rate_limited_requests = len([log for log in usage_logs if log.rate_limited])
        quota_exceeded_requests = len([log for log in usage_logs if log.quota_exceeded])
        
        # Calculate average response time
        response_times = [log.response_time_ms for log in usage_logs if log.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        # Calculate bytes transferred
        total_bytes_uploaded = sum(log.request_size_bytes or 0 for log in usage_logs)
        total_bytes_downloaded = sum(log.response_size_bytes or 0 for log in usage_logs)
        
        # Last 24h and 7d requests
        last_24h = end_date - timedelta(hours=24)
        last_7d = end_date - timedelta(days=7)
        
        last_24h_requests = len([log for log in usage_logs if log.timestamp >= last_24h])
        last_7d_requests = len([log for log in usage_logs if log.timestamp >= last_7d])
        
        # Top endpoints
        endpoint_counts = {}
        for log in usage_logs:
            endpoint_counts[log.endpoint] = endpoint_counts.get(log.endpoint, 0) + 1
        
        top_endpoints = [
            {"endpoint": endpoint, "count": count}
            for endpoint, count in sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return APIKeyUsageStats(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            rate_limited_requests=rate_limited_requests,
            quota_exceeded_requests=quota_exceeded_requests,
            average_response_time_ms=avg_response_time,
            total_bytes_uploaded=total_bytes_uploaded,
            total_bytes_downloaded=total_bytes_downloaded,
            last_24h_requests=last_24h_requests,
            last_7d_requests=last_7d_requests,
            top_endpoints=top_endpoints
        )
    
    def cleanup_expired_keys(self, db: Session) -> int:
        """Clean up expired API keys."""
        expired_keys = db.query(APIKey).filter(
            and_(
                APIKey.expires_at < datetime.utcnow(),
                APIKey.status == APIKeyStatus.ACTIVE.value
            )
        ).all()
        
        count = 0
        for key in expired_keys:
            key.status = APIKeyStatus.EXPIRED.value
            count += 1
        
        if count > 0:
            db.commit()
            logger.info(f"Marked {count} API keys as expired")
        
        return count

# Create singleton instance
api_key_service = APIKeyManagementService()