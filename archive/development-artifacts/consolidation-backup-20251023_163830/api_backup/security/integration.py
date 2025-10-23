#!/usr/bin/env python3
"""
T026 Security Hardening: Integration Service
Integrates all security components into the main application.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from fastapi import Request, Response, HTTPException, Depends
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.security.comprehensive_security import (
    SecurityHardening, SecurityConfig, security_hardening
)
from api.security.audit_models import (
    SecurityAuditLog, APIKeyAudit, SecurityIncident,
    AuditEventType, AuditSeverity
)
from api.utils.logger import get_system_logger

logger = get_system_logger("security_integration")

class SecurityIntegrationService:
    """Integration service for all T026 security components."""
    
    def __init__(self):
        self.security = security_hardening
        self.rate_limit_cache: Dict[str, List[float]] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.banned_ips: Dict[str, datetime] = {}
        
    def validate_and_audit_request(
        self,
        request: Request,
        db: Session,
        user_id: Optional[str] = None,
        endpoint_type: str = "api"
    ) -> Dict[str, Any]:
        """Comprehensive request validation and audit logging."""
        start_time = time.time()
        
        # Get client IP and basic info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Check if IP is banned
        if self._is_ip_banned(client_ip):
            self._log_audit_event(
                db, AuditEventType.SECURITY_VIOLATION, AuditSeverity.HIGH,
                request, user_id, "Access attempt from banned IP",
                {"reason": "banned_ip", "client_ip": client_ip}
            )
            raise HTTPException(
                status_code=429,
                detail="Access temporarily restricted"
            )
        
        # Rate limiting check
        if self._check_rate_limit(client_ip, endpoint_type):
            self._log_audit_event(
                db, AuditEventType.RATE_LIMIT_VIOLATION, AuditSeverity.MEDIUM,
                request, user_id, "Rate limit exceeded",
                {"client_ip": client_ip, "endpoint_type": endpoint_type}
            )
            
            # Increase failed attempts and potentially ban IP
            self.failed_attempts[client_ip] = self.failed_attempts.get(client_ip, 0) + 1
            if self.failed_attempts[client_ip] >= self.security.config.rate_limit_ban_threshold:
                self._ban_ip(client_ip)
                
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Validate request security
        security_info = self.security.validate_request_security(request)
        if not security_info["secure"]:
            self._log_audit_event(
                db, AuditEventType.SUSPICIOUS_INPUT, AuditSeverity.HIGH,
                request, user_id, "Suspicious request patterns detected",
                security_info
            )
        
        # Log successful API access
        processing_time = int((time.time() - start_time) * 1000)
        self._log_audit_event(
            db, AuditEventType.API_ACCESS, AuditSeverity.LOW,
            request, user_id, f"API access: {request.method} {request.url.path}",
            {"processing_time_ms": processing_time}
        )
        
        return security_info
    
    def log_authentication_event(
        self,
        db: Session,
        request: Request,
        username: str,
        success: bool,
        user_id: Optional[str] = None,
        failure_reason: Optional[str] = None
    ):
        """Log authentication events with security context."""
        event_type = AuditEventType.AUTH_SUCCESS if success else AuditEventType.AUTH_FAILURE
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM
        
        description = f"Authentication {'successful' if success else 'failed'} for user: {username}"
        details = {"username": username}
        
        if not success:
            client_ip = self._get_client_ip(request)
            self.failed_attempts[client_ip] = self.failed_attempts.get(client_ip, 0) + 1
            
            if failure_reason:
                details["failure_reason"] = failure_reason
            
            # Check for account lockout
            if self.failed_attempts[client_ip] >= self.security.config.auth_max_attempts:
                severity = AuditSeverity.HIGH
                details["action_taken"] = "ip_monitoring"
                
                # Create security incident for repeated failures
                self._create_security_incident(
                    db, "repeated_auth_failures",
                    f"Multiple authentication failures from {client_ip}",
                    f"IP {client_ip} has {self.failed_attempts[client_ip]} failed authentication attempts",
                    AuditSeverity.HIGH, client_ip
                )
        else:
            # Reset failed attempts on successful login
            client_ip = self._get_client_ip(request)
            if client_ip in self.failed_attempts:
                del self.failed_attempts[client_ip]
        
        self._log_audit_event(
            db, event_type, severity, request, user_id, description, details
        )
    
    def log_file_operation(
        self,
        db: Session,
        request: Request,
        operation: str,  # upload, download, delete
        filename: str,
        user_id: str,
        file_size: Optional[int] = None,
        success: bool = True
    ):
        """Log file operations with security validation."""
        # Validate filename
        try:
            sanitized_filename = self.security.input_validator.validate_filename(filename)
        except HTTPException as e:
            self._log_audit_event(
                db, AuditEventType.SUSPICIOUS_INPUT, AuditSeverity.HIGH,
                request, user_id, f"Suspicious filename in {operation}",
                {"filename": filename, "error": str(e.detail)}
            )
            raise
        
        event_type = AuditEventType.FILE_UPLOAD if operation == "upload" else AuditEventType.FILE_DOWNLOAD
        description = f"File {operation}: {sanitized_filename}"
        details = {
            "operation": operation,
            "filename": sanitized_filename,
            "success": success
        }
        
        if file_size:
            details["file_size"] = file_size
            
            # Check for unusually large files
            if file_size > self.security.config.max_file_size:
                self._log_audit_event(
                    db, AuditEventType.SUSPICIOUS_INPUT, AuditSeverity.MEDIUM,
                    request, user_id, "Large file upload attempt",
                    {"filename": sanitized_filename, "size": file_size}
                )
        
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM
        self._log_audit_event(
            db, event_type, severity, request, user_id, description, details
        )
    
    def log_admin_action(
        self,
        db: Session,
        request: Request,
        admin_user_id: str,
        action: str,
        target: str,
        details: Optional[Dict] = None
    ):
        """Log administrative actions with high security priority."""
        description = f"Admin action: {action} on {target}"
        audit_details = {
            "action": action,
            "target": target,
            "admin_user": admin_user_id
        }
        
        if details:
            audit_details.update(details)
        
        self._log_audit_event(
            db, AuditEventType.ADMIN_ACTION, AuditSeverity.HIGH,
            request, admin_user_id, description, audit_details
        )
    
    def validate_api_key(self, api_key: str, db: Session, request: Request) -> Optional[Dict]:
        """Validate API key and log usage."""
        key_info = self.security.api_key_manager.validate_api_key(api_key)
        
        if not key_info:
            self._log_audit_event(
                db, AuditEventType.SECURITY_VIOLATION, AuditSeverity.MEDIUM,
                request, None, "Invalid API key used",
                {"api_key_prefix": api_key[:10] + "..."}
            )
            return None
        
        # Log API key usage
        self._log_api_key_usage(db, request, api_key, key_info)
        return key_info
    
    def get_security_dashboard_data(self, db: Session, hours: int = 24) -> Dict[str, Any]:
        """Get security dashboard data for admin interface."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Query audit logs
        total_events = db.query(SecurityAuditLog).filter(
            SecurityAuditLog.timestamp >= since
        ).count()
        
        security_violations = db.query(SecurityAuditLog).filter(
            SecurityAuditLog.timestamp >= since,
            SecurityAuditLog.severity.in_([AuditSeverity.HIGH, AuditSeverity.CRITICAL])
        ).count()
        
        auth_failures = db.query(SecurityAuditLog).filter(
            SecurityAuditLog.timestamp >= since,
            SecurityAuditLog.event_type == AuditEventType.AUTH_FAILURE
        ).count()
        
        rate_limit_violations = db.query(SecurityAuditLog).filter(
            SecurityAuditLog.timestamp >= since,
            SecurityAuditLog.event_type == AuditEventType.RATE_LIMIT_VIOLATION
        ).count()
        
        # Active security incidents
        open_incidents = db.query(SecurityIncident).filter(
            SecurityIncident.status == "open"
        ).count()
        
        return {
            "period_hours": hours,
            "total_events": total_events,
            "security_violations": security_violations,
            "auth_failures": auth_failures,
            "rate_limit_violations": rate_limit_violations,
            "open_incidents": open_incidents,
            "banned_ips": len(self.banned_ips),
            "active_monitors": len(self.failed_attempts)
        }
    
    def _check_rate_limit(self, client_ip: str, endpoint_type: str) -> bool:
        """Check if client has exceeded rate limits."""
        now = time.time()
        window = 60  # 1 minute window
        
        if client_ip not in self.rate_limit_cache:
            self.rate_limit_cache[client_ip] = []
        
        # Clean old requests outside the window
        self.rate_limit_cache[client_ip] = [
            req_time for req_time in self.rate_limit_cache[client_ip]
            if now - req_time < window
        ]
        
        # Check rate limit
        if len(self.rate_limit_cache[client_ip]) >= self.security.config.rate_limit_requests_per_minute:
            return True
        
        # Add current request
        self.rate_limit_cache[client_ip].append(now)
        return False
    
    def _is_ip_banned(self, client_ip: str) -> bool:
        """Check if IP is currently banned."""
        if client_ip not in self.banned_ips:
            return False
        
        ban_expiry = self.banned_ips[client_ip]
        if datetime.utcnow() > ban_expiry:
            del self.banned_ips[client_ip]
            return False
        
        return True
    
    def _ban_ip(self, client_ip: str):
        """Ban an IP address for security violations."""
        ban_until = datetime.utcnow() + timedelta(seconds=self.security.config.rate_limit_ban_duration)
        self.banned_ips[client_ip] = ban_until
        logger.warning(f"IP {client_ip} banned until {ban_until}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        return self.security.audit_logger._get_client_ip(request)
    
    def _log_audit_event(
        self,
        db: Session,
        event_type: AuditEventType,
        severity: AuditSeverity,
        request: Request,
        user_id: Optional[str],
        description: str,
        details: Optional[Dict] = None
    ):
        """Log audit event to database."""
        audit_log = SecurityAuditLog(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_method=request.method,
            request_url=str(request.url),
            event_description=description,
            event_details=json.dumps(details) if details else None,
            risk_score=self._calculate_risk_score(event_type, severity, details),
            response_status=200  # Will be updated by middleware
        )
        
        db.add(audit_log)
        db.commit()
    
    def _log_api_key_usage(
        self,
        db: Session,
        request: Request,
        api_key: str,
        key_info: Dict
    ):
        """Log API key usage to audit trail."""
        api_audit = APIKeyAudit(
            timestamp=datetime.utcnow(),
            api_key_id=api_key[:10] + "...",  # Partial key for security
            user_id=key_info["user_id"],
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            request_method=request.method,
            request_url=str(request.url),
            permissions_used=",".join(key_info["permissions"]),
            success=True,
            response_time_ms=0  # Will be updated
        )
        
        db.add(api_audit)
        db.commit()
    
    def _create_security_incident(
        self,
        db: Session,
        incident_type: str,
        title: str,
        description: str,
        severity: AuditSeverity,
        source_ip: Optional[str] = None
    ):
        """Create a new security incident."""
        incident = SecurityIncident(
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            incident_type=incident_type,
            severity=severity,
            title=title,
            description=description,
            source_ip=source_ip,
            status="open"
        )
        
        db.add(incident)
        db.commit()
        
        logger.warning(f"Security incident created: {title}")
    
    def _calculate_risk_score(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        details: Optional[Dict]
    ) -> int:
        """Calculate risk score for an event."""
        base_scores = {
            AuditSeverity.LOW: 1,
            AuditSeverity.MEDIUM: 3,
            AuditSeverity.HIGH: 7,
            AuditSeverity.CRITICAL: 10
        }
        
        multipliers = {
            AuditEventType.AUTH_FAILURE: 2,
            AuditEventType.RATE_LIMIT_VIOLATION: 2,
            AuditEventType.SUSPICIOUS_INPUT: 3,
            AuditEventType.SECURITY_VIOLATION: 4,
            AuditEventType.ADMIN_ACTION: 1.5
        }
        
        base_score = base_scores.get(severity, 1)
        multiplier = multipliers.get(event_type, 1)
        
        return int(base_score * multiplier)

# Global security integration service
security_service = SecurityIntegrationService()