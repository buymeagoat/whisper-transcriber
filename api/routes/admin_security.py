#!/usr/bin/env python3
"""
T026 Security Hardening: Admin Security Routes
API endpoints for security monitoring and management.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from api.orm_bootstrap import get_db
from api.routes.auth import get_current_admin_user
from api.security.audit_models import (
    SecurityAuditLog, APIKeyAudit, SecurityIncident,
    AuditEventType, AuditSeverity
)
from api.security.integration import security_service
from api.utils.logger import get_system_logger

logger = get_system_logger("security_admin")
router = APIRouter(prefix="/admin/security", tags=["admin", "security"])

# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class SecurityDashboardResponse(BaseModel):
    """Security dashboard overview."""
    period_hours: int
    total_events: int
    security_violations: int
    auth_failures: int
    rate_limit_violations: int
    open_incidents: int
    banned_ips: int
    active_monitors: int
    risk_trend: List[Dict[str, Any]]

class AuditLogResponse(BaseModel):
    """Audit log entry response."""
    id: int
    timestamp: datetime
    event_type: str
    severity: str
    user_id: Optional[str]
    client_ip: Optional[str]
    request_method: Optional[str]
    request_url: Optional[str]
    event_description: str
    risk_score: Optional[int]
    blocked: bool

class SecurityIncidentResponse(BaseModel):
    """Security incident response."""
    id: int
    created_at: datetime
    incident_type: str
    severity: str
    status: str
    title: str
    description: str
    source_ip: Optional[str]
    assigned_to: Optional[str]

class APIKeyResponse(BaseModel):
    """API key information response."""
    key_id: str
    user_id: str
    permissions: List[str]
    created_at: datetime
    last_used: Optional[datetime]
    active: bool
    usage_count: int

# ─────────────────────────────────────────────────────────────────────────────
# Dashboard and Overview Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive security dashboard data."""
    
    # Log admin access
    security_service.log_admin_action(
        db, request, current_user.username, "view_security_dashboard", "dashboard"
    )
    
    # Get basic dashboard data
    dashboard_data = security_service.get_security_dashboard_data(db, hours)
    
    # Calculate risk trend
    risk_trend = await _calculate_risk_trend(db, hours)
    dashboard_data["risk_trend"] = risk_trend
    
    return SecurityDashboardResponse(**dashboard_data)

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: Optional[AuditEventType] = None,
    severity: Optional[AuditSeverity] = None,
    user_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    hours: int = Query(24, ge=1, le=168),
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering and pagination."""
    
    security_service.log_admin_action(
        db, request, current_user.username, "view_audit_logs", "audit_logs"
    )
    
    since = datetime.utcnow() - timedelta(hours=hours)
    query = db.query(SecurityAuditLog).filter(SecurityAuditLog.timestamp >= since)
    
    # Apply filters
    if event_type:
        query = query.filter(SecurityAuditLog.event_type == event_type)
    if severity:
        query = query.filter(SecurityAuditLog.severity == severity)
    if user_id:
        query = query.filter(SecurityAuditLog.user_id == user_id)
    if client_ip:
        query = query.filter(SecurityAuditLog.client_ip == client_ip)
    
    # Order by timestamp (newest first) and paginate
    logs = query.order_by(desc(SecurityAuditLog.timestamp)).offset(offset).limit(limit).all()
    
    return [
        AuditLogResponse(
            id=log.id,
            timestamp=log.timestamp,
            event_type=log.event_type.value,
            severity=log.severity.value,
            user_id=log.user_id,
            client_ip=log.client_ip,
            request_method=log.request_method,
            request_url=log.request_url,
            event_description=log.event_description,
            risk_score=log.risk_score,
            blocked=log.blocked
        )
        for log in logs
    ]

@router.get("/incidents", response_model=List[SecurityIncidentResponse])
async def get_security_incidents(
    status: Optional[str] = Query(None, regex="^(open|investigating|resolved)$"),
    severity: Optional[AuditSeverity] = None,
    limit: int = Query(50, ge=1, le=200),
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get security incidents with filtering."""
    
    security_service.log_admin_action(
        db, request, current_user.username, "view_security_incidents", "incidents"
    )
    
    query = db.query(SecurityIncident)
    
    if status:
        query = query.filter(SecurityIncident.status == status)
    if severity:
        query = query.filter(SecurityIncident.severity == severity)
    
    incidents = query.order_by(desc(SecurityIncident.created_at)).limit(limit).all()
    
    return [
        SecurityIncidentResponse(
            id=incident.id,
            created_at=incident.created_at,
            incident_type=incident.incident_type,
            severity=incident.severity.value,
            status=incident.status,
            title=incident.title,
            description=incident.description,
            source_ip=incident.source_ip,
            assigned_to=incident.assigned_to
        )
        for incident in incidents
    ]

# ─────────────────────────────────────────────────────────────────────────────
# API Key Management Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api-keys")
async def create_api_key(
    user_id: str,
    permissions: List[str],
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for a user."""
    
    # Validate permissions
    valid_permissions = {"read", "write", "admin", "upload", "download"}
    if not all(perm in valid_permissions for perm in permissions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid permissions. Valid options: {valid_permissions}"
        )
    
    # Generate API key
    api_key = security_service.security.api_key_manager.generate_api_key(user_id, permissions)
    
    # Log admin action
    security_service.log_admin_action(
        db, request, current_user.username, "create_api_key", user_id,
        {"permissions": permissions}
    )
    
    return {
        "api_key": api_key,
        "user_id": user_id,
        "permissions": permissions,
        "created_at": datetime.utcnow().isoformat()
    }

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all API keys with usage statistics."""
    
    security_service.log_admin_action(
        db, request, current_user.username, "list_api_keys", "all"
    )
    
    api_keys = []
    for key_id, key_info in security_service.security.api_key_manager.api_keys.items():
        # Get usage count from audit logs
        usage_count = db.query(APIKeyAudit).filter(
            APIKeyAudit.api_key_id == key_id[:10] + "..."
        ).count()
        
        api_keys.append(APIKeyResponse(
            key_id=key_id[:10] + "...",
            user_id=key_info["user_id"],
            permissions=key_info["permissions"],
            created_at=key_info["created_at"],
            last_used=key_info["last_used"],
            active=key_info["active"],
            usage_count=usage_count
        ))
    
    return api_keys

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key."""
    
    success = security_service.security.api_key_manager.revoke_api_key(key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    security_service.log_admin_action(
        db, request, current_user.username, "revoke_api_key", key_id
    )
    
    return {"message": "API key revoked successfully"}

# ─────────────────────────────────────────────────────────────────────────────
# Security Configuration Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/config")
async def get_security_config(
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get current security configuration."""
    
    security_service.log_admin_action(
        db, request, current_user.username, "view_security_config", "config"
    )
    
    config = security_service.security.config
    return {
        "rate_limiting": {
            "requests_per_minute": config.rate_limit_requests_per_minute,
            "ban_threshold": config.rate_limit_ban_threshold,
            "ban_duration": config.rate_limit_ban_duration
        },
        "authentication": {
            "max_attempts": config.auth_max_attempts,
            "lockout_duration": config.auth_lockout_duration,
            "jwt_expiry": config.jwt_token_expiry
        },
        "file_security": {
            "max_file_size": config.max_file_size,
            "allowed_extensions": list(config.allowed_file_extensions)
        },
        "audit_logging": {
            "log_all_requests": config.audit_log_all_requests,
            "retention_days": config.audit_retention_days
        }
    }

@router.get("/statistics")
async def get_security_statistics(
    days: int = Query(7, ge=1, le=30),
    request: Request = None,
    current_user = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get security statistics over time."""
    
    security_service.log_admin_action(
        db, request, current_user.username, "view_security_stats", "statistics"
    )
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Daily event counts
    daily_stats = db.query(
        func.date(SecurityAuditLog.timestamp).label('date'),
        func.count(SecurityAuditLog.id).label('total_events'),
        func.sum(func.case(
            (SecurityAuditLog.event_type == AuditEventType.AUTH_FAILURE, 1),
            else_=0
        )).label('auth_failures'),
        func.sum(func.case(
            (SecurityAuditLog.event_type == AuditEventType.RATE_LIMIT_VIOLATION, 1),
            else_=0
        )).label('rate_violations')
    ).filter(
        SecurityAuditLog.timestamp >= since
    ).group_by(
        func.date(SecurityAuditLog.timestamp)
    ).order_by('date').all()
    
    return {
        "period_days": days,
        "daily_statistics": [
            {
                "date": stat.date.isoformat(),
                "total_events": stat.total_events,
                "auth_failures": stat.auth_failures or 0,
                "rate_violations": stat.rate_violations or 0
            }
            for stat in daily_stats
        ]
    }

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

async def _calculate_risk_trend(db: Session, hours: int) -> List[Dict[str, Any]]:
    """Calculate risk score trend over time."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get hourly risk scores
    hourly_risk = db.query(
        func.date_trunc('hour', SecurityAuditLog.timestamp).label('hour'),
        func.avg(SecurityAuditLog.risk_score).label('avg_risk'),
        func.max(SecurityAuditLog.risk_score).label('max_risk'),
        func.count(SecurityAuditLog.id).label('event_count')
    ).filter(
        SecurityAuditLog.timestamp >= since,
        SecurityAuditLog.risk_score.isnot(None)
    ).group_by(
        func.date_trunc('hour', SecurityAuditLog.timestamp)
    ).order_by('hour').all()
    
    return [
        {
            "hour": risk.hour.isoformat(),
            "avg_risk": float(risk.avg_risk or 0),
            "max_risk": risk.max_risk or 0,
            "event_count": risk.event_count
        }
        for risk in hourly_risk
    ]