"""
Admin routes for audit log viewing and management
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status

from api.routes.auth import require_admin
from api.models import User
from api.services.audit_logging import (
    audit_logger, 
    AuditEventType, 
    AuditSeverity
)


router = APIRouter()


@router.get("/audit-logs")
async def get_audit_logs(
    admin_user: User = Depends(require_admin),
    limit: int = Query(default=100, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(default=0, ge=0, description="Number of logs to skip"),
    event_type: Optional[str] = Query(default=None, description="Filter by event type"),
    severity: Optional[str] = Query(default=None, description="Filter by severity level"),
    user_id: Optional[int] = Query(default=None, description="Filter by user ID"),
    client_ip: Optional[str] = Query(default=None, description="Filter by client IP"),
    start_date: Optional[str] = Query(default=None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(default=None, description="End date (ISO format)"),
):
    """
    Retrieve audit logs with optional filtering
    
    Requires admin privileges.
    """
    
    # Parse date filters
    start_time = None
    end_time = None
    
    if start_date:
        try:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
    
    if end_date:
        try:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
    
    # Validate enum values
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            valid_types = [e.value for e in AuditEventType]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event_type. Valid values: {valid_types}"
            )
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AuditSeverity(severity)
        except ValueError:
            valid_severities = [s.value for s in AuditSeverity]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity. Valid values: {valid_severities}"
            )
    
    # Fetch audit logs
    logs = await audit_logger.get_audit_logs(
        limit=limit,
        offset=offset,
        event_type=event_type_enum,
        severity=severity_enum,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        client_ip=client_ip
    )
    
    return {
        "logs": logs,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "returned_count": len(logs)
        },
        "filters": {
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "client_ip": client_ip,
            "start_date": start_date,
            "end_date": end_date
        }
    }


@router.get("/audit-stats")
async def get_audit_statistics(
    admin_user: User = Depends(require_admin)
):
    """
    Get audit log statistics
    
    Requires admin privileges.
    """
    
    stats = await audit_logger.get_audit_stats()
    return stats


@router.get("/audit-event-types")
async def get_audit_event_types(
    admin_user: User = Depends(require_admin)
):
    """
    Get list of available audit event types
    
    Requires admin privileges.
    """
    
    return {
        "event_types": [
            {
                "value": event_type.value,
                "name": event_type.value.replace("_", " ").title()
            }
            for event_type in AuditEventType
        ],
        "severity_levels": [
            {
                "value": severity.value,
                "name": severity.value.title()
            }
            for severity in AuditSeverity
        ]
    }


@router.get("/audit-recent-alerts")
async def get_recent_security_alerts(
    admin_user: User = Depends(require_admin),
    hours: int = Query(default=24, le=168, description="Number of hours to look back")
):
    """
    Get recent high-severity security events
    
    Requires admin privileges.
    """
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get high and critical severity events
    high_severity_logs = await audit_logger.get_audit_logs(
        limit=50,
        severity=AuditSeverity.HIGH,
        start_time=start_time
    )
    
    critical_severity_logs = await audit_logger.get_audit_logs(
        limit=50,
        severity=AuditSeverity.CRITICAL,
        start_time=start_time
    )
    
    # Combine and sort by timestamp
    all_alerts = high_severity_logs + critical_severity_logs
    all_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return {
        "alerts": all_alerts[:50],  # Limit to 50 most recent
        "time_range_hours": hours,
        "high_severity_count": len(high_severity_logs),
        "critical_severity_count": len(critical_severity_logs)
    }
