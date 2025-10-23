#!/usr/bin/env python3
"""
T027 Advanced Features: API Key Management Models
Database models for developer API key management system.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from api.orm_bootstrap import Base

class APIKeyStatus(Enum):
    """API key status enumeration."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class APIKeyPermission(Enum):
    """API key permission levels."""
    READ = "read"               # Read-only access to jobs and data
    WRITE = "write"             # Create and modify jobs
    DELETE = "delete"           # Delete jobs and data
    ADMIN = "admin"             # Administrative access
    BATCH = "batch"             # Batch processing permissions
    ANALYTICS = "analytics"     # Access to usage analytics

class APIKey(Base):
    """API key model for developer access."""
    __tablename__ = "api_keys"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String(255), unique=True, nullable=False, index=True)  # Public identifier
    key_hash = Column(String(255), nullable=False, index=True)  # Hashed key value
    key_prefix = Column(String(20), nullable=False)  # First 8 chars for identification
    
    # Key metadata
    name = Column(String(255), nullable=False)  # User-friendly name
    description = Column(Text, nullable=True)  # Optional description
    
    # Ownership and permissions
    user_id = Column(String(255), nullable=False, index=True)  # Owner user ID
    permissions = Column(JSON, nullable=False)  # List of APIKeyPermission values
    
    # Status and lifecycle
    status = Column(String(20), nullable=False, default=APIKeyStatus.ACTIVE.value, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, index=True)  # NULL = no expiration
    last_used_at = Column(DateTime, nullable=True, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(255), nullable=True)  # User ID who revoked
    revoked_reason = Column(Text, nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_ip = Column(String(45), nullable=True)  # IPv4/IPv6
    last_used_user_agent = Column(Text, nullable=True)
    
    # Rate limiting and quotas
    rate_limit_per_hour = Column(Integer, nullable=True)  # NULL = use default
    daily_quota = Column(Integer, nullable=True)  # NULL = unlimited
    monthly_quota = Column(Integer, nullable=True)  # NULL = unlimited
    
    # Metadata and configuration
    allowed_ips = Column(JSON, nullable=True)  # List of allowed IP addresses/ranges
    key_metadata = Column(JSON, nullable=True)  # Additional key-specific data
    
    # Relationships
    usage_logs = relationship("APIKeyUsageLog", back_populates="api_key", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<APIKey(key_id='{self.key_id}', name='{self.name}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if the API key is currently active."""
        if self.status != APIKeyStatus.ACTIVE.value:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    @property
    def permissions_list(self) -> List[str]:
        """Get permissions as a list of strings."""
        if isinstance(self.permissions, list):
            return self.permissions
        return []
    
    def has_permission(self, permission: str) -> bool:
        """Check if the key has a specific permission."""
        return permission in self.permissions_list
    
    def update_usage(self, ip_address: str = None, user_agent: str = None):
        """Update usage statistics."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        if ip_address:
            self.last_used_ip = ip_address
        if user_agent:
            self.last_used_user_agent = user_agent

class APIKeyUsageLog(Base):
    """Detailed usage logging for API keys."""
    __tablename__ = "api_key_usage_logs"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    
    # Request details
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    method = Column(String(10), nullable=False)  # HTTP method
    endpoint = Column(String(255), nullable=False, index=True)  # Request path
    status_code = Column(Integer, nullable=False, index=True)  # Response status
    response_time_ms = Column(Integer, nullable=True)  # Response time in milliseconds
    
    # Client information
    client_ip = Column(String(45), nullable=False, index=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    
    # Request/response data
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)  # If status_code >= 400
    
    # Additional metadata
    rate_limited = Column(Boolean, nullable=False, default=False, index=True)
    quota_exceeded = Column(Boolean, nullable=False, default=False, index=True)
    usage_metadata = Column(JSON, nullable=True)
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    
    def __repr__(self):
        return f"<APIKeyUsageLog(api_key_id={self.api_key_id}, endpoint='{self.endpoint}', status={self.status_code})>"

class APIKeyQuotaUsage(Base):
    """Track API key quota usage by time period."""
    __tablename__ = "api_key_quota_usage"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False, index=True)
    
    # Time period tracking
    period_type = Column(String(20), nullable=False, index=True)  # 'hourly', 'daily', 'monthly'
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    
    # Usage statistics
    request_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    total_bytes_uploaded = Column(Integer, nullable=False, default=0)
    total_bytes_downloaded = Column(Integer, nullable=False, default=0)
    total_response_time_ms = Column(Integer, nullable=False, default=0)
    
    # Quota tracking
    quota_limit = Column(Integer, nullable=True)  # The limit that was in effect
    quota_exceeded = Column(Boolean, nullable=False, default=False)
    first_quota_exceeded_at = Column(DateTime, nullable=True)
    
    # Metadata
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<APIKeyQuotaUsage(api_key_id={self.api_key_id}, period='{self.period_type}', requests={self.request_count})>"
    
    @property
    def average_response_time_ms(self) -> float:
        """Calculate average response time."""
        if self.request_count == 0:
            return 0.0
        return self.total_response_time_ms / self.request_count
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.request_count == 0:
            return 0.0
        return (self.success_count / self.request_count) * 100

# Create indexes for performance optimization
from sqlalchemy import Index

# Composite indexes for common query patterns
api_key_user_status_idx = Index('idx_api_keys_user_status', APIKey.user_id, APIKey.status)
api_key_expires_status_idx = Index('idx_api_keys_expires_status', APIKey.expires_at, APIKey.status)

usage_log_key_time_idx = Index('idx_usage_logs_key_time', APIKeyUsageLog.api_key_id, APIKeyUsageLog.timestamp)
usage_log_endpoint_time_idx = Index('idx_usage_logs_endpoint_time', APIKeyUsageLog.endpoint, APIKeyUsageLog.timestamp)
usage_log_ip_time_idx = Index('idx_usage_logs_ip_time', APIKeyUsageLog.client_ip, APIKeyUsageLog.timestamp)

quota_usage_key_period_idx = Index('idx_quota_usage_key_period', APIKeyQuotaUsage.api_key_id, APIKeyQuotaUsage.period_type, APIKeyQuotaUsage.period_start)