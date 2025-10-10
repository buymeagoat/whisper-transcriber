"""
Comprehensive audit logging system for security events and user actions
"""
import json
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import Request

from api.utils.logger import get_system_logger
from api.orm_bootstrap import SessionLocal
from api.models import Base, AuditLog


logger = get_system_logger()


class AuditEventType(str, Enum):
    """Types of events to audit"""
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_REGISTRATION = "account_registration"
    
    # Authorization events
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    
    # File operations
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    
    # Job operations
    JOB_CREATE = "job_create"
    JOB_DELETE = "job_delete"
    JOB_UPDATE = "job_update"
    
    # Admin operations
    USER_CREATE = "user_create"
    USER_DELETE = "user_delete"
    USER_UPDATE = "user_update"
    SETTINGS_CHANGE = "settings_change"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System events
    SERVER_START = "server_start"
    SERVER_STOP = "server_stop"
    ERROR = "error"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


logger = get_system_logger()


class AuditLogger:
    """Main audit logging service"""
    
    def __init__(self):
        self.db_session = SessionLocal
        
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """Extract session ID from request"""
        # Try to get from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use first 8 chars of token as session identifier
            token = auth_header[7:]
            return token[:8] if len(token) >= 8 else token
        
        # Fallback to session cookie if available
        return request.cookies.get("session_id")
    
    async def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        request: Optional[Request] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None
    ):
        """Log an audit event"""
        
        try:
            # Extract request information if available
            client_ip = None
            user_agent = None
            endpoint = None
            method = None
            session_id = None
            
            if request:
                client_ip = self._get_client_ip(request)
                user_agent = request.headers.get("User-Agent")
                endpoint = str(request.url.path)
                method = request.method
                session_id = self._get_session_id(request)
            
            # Create audit log entry
            audit_entry = AuditLog(
                timestamp=datetime.utcnow(),
                event_type=event_type.value,
                severity=severity.value,
                user_id=user_id,
                username=username,
                client_ip=client_ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                resource_id=resource_id,
                resource_type=resource_type,
                details=json.dumps(details) if details else None,
                session_id=session_id
            )
            
            # Save to database
            db = self.db_session()
            try:
                db.add(audit_entry)
                db.commit()
                
                # Also log to system logger for immediate visibility
                log_message = (
                    f"AUDIT: {event_type.value} | "
                    f"User: {username or 'anonymous'} | "
                    f"IP: {client_ip or 'unknown'} | "
                    f"Endpoint: {endpoint or 'N/A'}"
                )
                
                if severity == AuditSeverity.CRITICAL:
                    logger.critical(log_message)
                elif severity == AuditSeverity.HIGH:
                    logger.warning(log_message)
                else:
                    logger.info(log_message)
                    
            finally:
                db.close()
                
        except Exception as e:
            # Never fail the main application due to audit logging issues
            logger.error(f"Audit logging failed: {e}")
    
    async def get_audit_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        user_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        client_ip: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering"""
        
        db = self.db_session()
        try:
            query = db.query(AuditLog)
            
            # Apply filters
            if event_type:
                query = query.filter(AuditLog.event_type == event_type.value)
            if severity:
                query = query.filter(AuditLog.severity == severity.value)
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            if start_time:
                query = query.filter(AuditLog.timestamp >= start_time)
            if end_time:
                query = query.filter(AuditLog.timestamp <= end_time)
            if client_ip:
                query = query.filter(AuditLog.client_ip == client_ip)
            
            # Order by timestamp (newest first) and apply pagination
            query = query.order_by(AuditLog.timestamp.desc())
            query = query.offset(offset).limit(limit)
            
            # Convert to dict format
            logs = []
            for log in query.all():
                log_dict = {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "event_type": log.event_type,
                    "severity": log.severity,
                    "user_id": log.user_id,
                    "username": log.username,
                    "client_ip": log.client_ip,
                    "user_agent": log.user_agent,
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "status_code": log.status_code,
                    "resource_id": log.resource_id,
                    "resource_type": log.resource_type,
                    "session_id": log.session_id,
                    "details": json.loads(log.details) if log.details else None
                }
                logs.append(log_dict)
            
            return logs
            
        finally:
            db.close()
    
    async def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        
        db = self.db_session()
        try:
            # Basic counts
            total_events = db.query(AuditLog).count()
            
            # Recent activity (last 24 hours)
            from datetime import timedelta
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_events = db.query(AuditLog).filter(
                AuditLog.timestamp >= yesterday
            ).count()
            
            # Events by severity
            severity_counts = {}
            for severity in AuditSeverity:
                count = db.query(AuditLog).filter(
                    AuditLog.severity == severity.value
                ).count()
                severity_counts[severity.value] = count
            
            # Most common event types (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            event_type_query = db.query(
                AuditLog.event_type,
                db.func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.timestamp >= week_ago
            ).group_by(
                AuditLog.event_type
            ).order_by(
                db.func.count(AuditLog.id).desc()
            ).limit(10)
            
            top_event_types = [
                {"event_type": row.event_type, "count": row.count}
                for row in event_type_query.all()
            ]
            
            return {
                "total_events": total_events,
                "recent_events_24h": recent_events,
                "severity_distribution": severity_counts,
                "top_event_types_7d": top_event_types
            }
            
        finally:
            db.close()


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for common audit events
async def log_authentication_event(
    event_type: AuditEventType,
    request: Request,
    username: str,
    success: bool = True,
    details: Optional[Dict[str, Any]] = None
):
    """Log authentication-related events"""
    severity = AuditSeverity.MEDIUM if success else AuditSeverity.HIGH
    await audit_logger.log_event(
        event_type=event_type,
        severity=severity,
        request=request,
        username=username,
        details=details
    )


async def log_file_operation(
    event_type: AuditEventType,
    request: Request,
    user_id: int,
    username: str,
    file_id: str,
    filename: str,
    details: Optional[Dict[str, Any]] = None
):
    """Log file operation events"""
    await audit_logger.log_event(
        event_type=event_type,
        severity=AuditSeverity.MEDIUM,
        request=request,
        user_id=user_id,
        username=username,
        resource_id=file_id,
        resource_type="file",
        details={**(details or {}), "filename": filename}
    )


async def log_security_event(
    event_type: AuditEventType,
    request: Request,
    severity: AuditSeverity = AuditSeverity.HIGH,
    details: Optional[Dict[str, Any]] = None
):
    """Log security-related events"""
    await audit_logger.log_event(
        event_type=event_type,
        severity=severity,
        request=request,
        details=details
    )


async def log_admin_action(
    event_type: AuditEventType,
    request: Request,
    admin_user_id: int,
    admin_username: str,
    target_resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log administrative actions"""
    await audit_logger.log_event(
        event_type=event_type,
        severity=AuditSeverity.HIGH,
        request=request,
        user_id=admin_user_id,
        username=admin_username,
        resource_id=target_resource_id,
        details=details
    )
