#!/usr/bin/env python3
"""
T026 Security Hardening: Audit Logging Database Models
Defines database models for comprehensive audit logging.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import DateTime, Enum, Integer, String, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from api.orm_bootstrap import Base

class AuditEventType(str, PyEnum):
    """Enumeration of audit event types."""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOGOUT = "auth_logout"
    PASSWORD_CHANGE = "password_change"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    SUSPICIOUS_INPUT = "suspicious_input"
    SUSPICIOUS_HEADER = "suspicious_header"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    API_ACCESS = "api_access"
    ADMIN_ACTION = "admin_action"
    DATA_EXPORT = "data_export"
    SYSTEM_ACCESS = "system_access"
    SECURITY_VIOLATION = "security_violation"

class AuditSeverity(str, PyEnum):
    """Audit event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityAuditLog(Base):
    """Comprehensive security audit log model."""
    
    __tablename__ = "security_audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType), nullable=False, index=True)
    severity: Mapped[AuditSeverity] = mapped_column(Enum(AuditSeverity), nullable=False, default=AuditSeverity.MEDIUM)
    
    # User and session information
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Request information
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)  # IPv6 support
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    request_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_headers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Event details
    event_description: Mapped[str] = mapped_column(String(500), nullable=False)
    event_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON data
    
    # Security context
    risk_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Response information
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Composite indexes for efficient querying
    __table_args__ = (
        Index('idx_audit_time_type', 'timestamp', 'event_type'),
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_ip_time', 'client_ip', 'timestamp'),
        Index('idx_audit_severity_time', 'severity', 'timestamp'),
        Index('idx_audit_risk_time', 'risk_score', 'timestamp'),
    )

class APIKeyAudit(Base):
    """API key usage audit log."""
    
    __tablename__ = "api_key_audit_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    api_key_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Request information
    client_ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    request_url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Usage tracking
    permissions_used: Mapped[str] = mapped_column(String(200), nullable=False)  # Comma-separated
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Performance tracking
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    
    __table_args__ = (
        Index('idx_api_key_time', 'api_key_id', 'timestamp'),
        Index('idx_api_user_time', 'user_id', 'timestamp'),
    )

class SecurityIncident(Base):
    """Security incident tracking."""
    
    __tablename__ = "security_incidents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[AuditSeverity] = mapped_column(Enum(AuditSeverity), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")  # open, investigating, resolved
    
    # Incident details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Source information
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    source_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Response information
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Related audit log entries
    related_audit_log_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    
    __table_args__ = (
        Index('idx_incident_status_severity', 'status', 'severity'),
        Index('idx_incident_type_time', 'incident_type', 'created_at'),
    )