"""
Secure Audit Logging System for Whisper Transcriber
Provides structured, tamper-resistant audit logging for security-sensitive operations.
"""

import logging
import json
import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from pathlib import Path
import re
import html

from api.utils.logger import get_system_logger

base_logger = get_system_logger("audit_logger")


class AuditEventType(str, Enum):
    """Standardized audit event types"""
    
    # Authentication Events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET = "auth.password.reset"
    ACCOUNT_LOCKED = "auth.account.locked"
    ACCOUNT_UNLOCKED = "auth.account.unlocked"
    
    # Authorization Events
    ACCESS_GRANTED = "authz.access.granted"
    ACCESS_DENIED = "authz.access.denied"
    PRIVILEGE_ESCALATION = "authz.privilege.escalation"
    ROLE_CHANGE = "authz.role.change"
    
    # Data Events
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    DATA_IMPORT = "data.import"
    
    # File Events
    FILE_UPLOAD = "file.upload"
    FILE_DOWNLOAD = "file.download"
    FILE_DELETE = "file.delete"
    FILE_ACCESS = "file.access"
    
    # Administrative Events
    ADMIN_CONFIG_CHANGE = "admin.config.change"
    ADMIN_USER_CREATE = "admin.user.create"
    ADMIN_USER_DELETE = "admin.user.delete"
    ADMIN_BACKUP = "admin.backup"
    ADMIN_RESTORE = "admin.restore"
    
    # Security Events
    SECURITY_THREAT_DETECTED = "security.threat.detected"
    SECURITY_RATE_LIMIT = "security.rate_limit"
    SECURITY_BLOCKED_REQUEST = "security.blocked_request"
    SECURITY_VULNERABILITY = "security.vulnerability"
    
    # System Events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditOutcome(str, Enum):
    """Audit event outcomes"""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    UNKNOWN = "unknown"


class SecurityAuditLogger:
    """
    Secure audit logger with input sanitization and tamper protection.
    
    Features:
    - Input sanitization to prevent log injection
    - Structured JSON logging format
    - Integrity protection with checksums
    - Configurable retention and rotation
    - Performance monitoring
    """
    
    def __init__(self, 
                 logger_name: str = "security_audit",
                 log_file: Optional[str] = None,
                 enable_integrity: bool = True,
                 enable_encryption: bool = False):
        
        self.logger_name = logger_name
        self.enable_integrity = enable_integrity
        self.enable_encryption = enable_encryption
        
        # Performance tracking (initialize early)
        self.log_count = 0
        self.start_time = datetime.now(timezone.utc)
        
        # Setup logging
        self._setup_logger(log_file)
        
        # Integrity protection
        self.session_id = str(uuid.uuid4())
        self.sequence_number = 0
        self.last_hash = self._calculate_initial_hash()
        
        # Sanitization patterns
        self._setup_sanitization_patterns()
    
    def _setup_logger(self, log_file: Optional[str]):
        """Setup the underlying logger with secure configuration"""
        
        self.logger = logging.getLogger(self.logger_name)
        
        # Avoid duplicate handlers
        if self.logger.handlers:
            return
        
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory
        logs_dir = Path("logs/audit")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for audit logs
        audit_file = log_file or str(logs_dir / "security_audit.log")
        file_handler = logging.FileHandler(audit_file, mode='a', encoding='utf-8')
        
        # JSON formatter for structured logging
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.propagate = False  # Prevent propagation to root logger
    
    def _setup_sanitization_patterns(self):
        """Setup patterns for input sanitization"""
        
        # Patterns that could be used for log injection
        self.dangerous_patterns = [
            (r'[\r\n\f\t\v\x00-\x1f\x7f-\x9f]', ''),  # Control characters
            (r'\${[^}]*}', '[REMOVED]'),  # Variable substitution
            (r'%[a-zA-Z]', '[REMOVED]'),  # Format strings
            (r'<script[^>]*>.*?</script>', '[SCRIPT_REMOVED]'),  # Script tags
            (r'javascript:', '[JS_REMOVED]'),  # JavaScript URLs
            (r'data:.*?base64', '[DATA_URL_REMOVED]'),  # Data URLs
        ]
        
        # Compile regex patterns for performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE | re.DOTALL), replacement)
            for pattern, replacement in self.dangerous_patterns
        ]
    
    def _sanitize_input(self, data: Any) -> Any:
        """Sanitize input data to prevent log injection"""
        
        if isinstance(data, str):
            # Apply sanitization patterns
            sanitized = data
            for pattern, replacement in self.compiled_patterns:
                sanitized = pattern.sub(replacement, sanitized)
            
            # HTML escape for additional safety
            sanitized = html.escape(sanitized)
            
            # Limit length to prevent log flooding
            if len(sanitized) > 1000:
                sanitized = sanitized[:997] + "..."
            
            return sanitized
        
        elif isinstance(data, dict):
            return {key: self._sanitize_input(value) for key, value in data.items()}
        
        elif isinstance(data, list):
            return [self._sanitize_input(item) for item in data]
        
        elif isinstance(data, (int, float, bool, type(None))):
            return data
        
        else:
            # Convert other types to string and sanitize
            return self._sanitize_input(str(data))
    
    def _calculate_initial_hash(self) -> str:
        """Calculate initial hash for integrity chain"""
        initial_data = f"{self.session_id}:{self.start_time.isoformat()}"
        return hashlib.sha256(initial_data.encode()).hexdigest()
    
    def _calculate_entry_hash(self, log_entry: Dict[str, Any]) -> str:
        """Calculate hash for a log entry to maintain integrity chain"""
        
        if not self.enable_integrity:
            return ""
        
        # Create deterministic string representation
        entry_str = json.dumps(log_entry, sort_keys=True, separators=(',', ':'))
        
        # Include previous hash for chaining
        hash_data = f"{self.last_hash}:{entry_str}:{self.sequence_number}"
        
        return hashlib.sha256(hash_data.encode()).hexdigest()
    
    def _create_audit_entry(self,
                           event_type: AuditEventType,
                           message: str,
                           severity: AuditSeverity = AuditSeverity.MEDIUM,
                           outcome: AuditOutcome = AuditOutcome.SUCCESS,
                           user_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None,
                           resource: Optional[str] = None,
                           additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a structured audit log entry"""
        
        # Increment sequence number
        self.sequence_number += 1
        
        # Basic audit entry structure
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sequence": self.sequence_number,
            "session_id": self.session_id,
            "event_type": event_type.value,
            "message": self._sanitize_input(message),
            "severity": severity.value,
            "outcome": outcome.value,
            "logger": self.logger_name,
            "version": "1.0"
        }
        
        # Add user context if provided
        if user_id:
            entry["user_id"] = self._sanitize_input(user_id)
        
        if session_id:
            entry["user_session_id"] = self._sanitize_input(session_id)
        
        # Add network context if provided
        if ip_address:
            entry["ip_address"] = self._sanitize_input(ip_address)
        
        if user_agent:
            entry["user_agent"] = self._sanitize_input(user_agent)
        
        # Add resource information if provided
        if resource:
            entry["resource"] = self._sanitize_input(resource)
        
        # Add additional data if provided
        if additional_data:
            entry["additional_data"] = self._sanitize_input(additional_data)
        
        # Calculate integrity hash
        if self.enable_integrity:
            entry_hash = self._calculate_entry_hash(entry)
            entry["integrity_hash"] = entry_hash
            entry["previous_hash"] = self.last_hash
            self.last_hash = entry_hash
        
        return entry
    
    def log_audit_event(self,
                       event_type: AuditEventType,
                       message: str,
                       severity: AuditSeverity = AuditSeverity.MEDIUM,
                       outcome: AuditOutcome = AuditOutcome.SUCCESS,
                       user_id: Optional[str] = None,
                       session_id: Optional[str] = None,
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None,
                       resource: Optional[str] = None,
                       additional_data: Optional[Dict[str, Any]] = None):
        """
        Log a security audit event with full context.
        
        Args:
            event_type: Type of audit event
            message: Human-readable description
            severity: Event severity level
            outcome: Event outcome
            user_id: User identifier
            session_id: User session identifier
            ip_address: Client IP address
            user_agent: Client user agent
            resource: Resource being accessed
            additional_data: Additional context data
        """
        
        try:
            # Create audit entry
            entry = self._create_audit_entry(
                event_type=event_type,
                message=message,
                severity=severity,
                outcome=outcome,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource=resource,
                additional_data=additional_data
            )
            
            # Log as JSON
            self.logger.info(json.dumps(entry, separators=(',', ':')))
            
            # Update statistics
            self.log_count += 1
            
            # Log to system logger for high/critical severity
            if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                base_logger.warning(f"AUDIT {severity.value.upper()}: {message}")
        
        except Exception as e:
            # Fallback logging - never fail silently
            base_logger.error(f"Failed to log audit event: {e}")
            base_logger.info(f"Fallback audit log: {event_type.value} - {message}")
    
    def log_authentication_event(self,
                                user_id: str,
                                event_type: AuditEventType,
                                outcome: AuditOutcome,
                                ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None,
                                additional_details: Optional[Dict[str, Any]] = None):
        """Log authentication-related events"""
        
        severity = AuditSeverity.HIGH if outcome == AuditOutcome.FAILURE else AuditSeverity.MEDIUM
        message = f"Authentication event: {event_type.value} for user {user_id}"
        
        self.log_audit_event(
            event_type=event_type,
            message=message,
            severity=severity,
            outcome=outcome,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_details
        )
    
    def log_authorization_event(self,
                               user_id: str,
                               resource: str,
                               action: str,
                               outcome: AuditOutcome,
                               ip_address: Optional[str] = None,
                               additional_details: Optional[Dict[str, Any]] = None):
        """Log authorization-related events"""
        
        event_type = AuditEventType.ACCESS_GRANTED if outcome == AuditOutcome.SUCCESS else AuditEventType.ACCESS_DENIED
        severity = AuditSeverity.HIGH if outcome == AuditOutcome.FAILURE else AuditSeverity.LOW
        message = f"Authorization {outcome.value}: {action} on {resource} for user {user_id}"
        
        self.log_audit_event(
            event_type=event_type,
            message=message,
            severity=severity,
            outcome=outcome,
            user_id=user_id,
            resource=resource,
            ip_address=ip_address,
            additional_data=additional_details
        )
    
    def log_data_event(self,
                      user_id: str,
                      action: str,
                      resource: str,
                      outcome: AuditOutcome = AuditOutcome.SUCCESS,
                      ip_address: Optional[str] = None,
                      additional_details: Optional[Dict[str, Any]] = None):
        """Log data access/modification events"""
        
        event_type_map = {
            "create": AuditEventType.DATA_CREATE,
            "read": AuditEventType.DATA_READ,
            "update": AuditEventType.DATA_UPDATE,
            "delete": AuditEventType.DATA_DELETE,
            "export": AuditEventType.DATA_EXPORT,
            "import": AuditEventType.DATA_IMPORT
        }
        
        event_type = event_type_map.get(action.lower(), AuditEventType.DATA_READ)
        severity = AuditSeverity.HIGH if action.lower() in ["delete", "export"] else AuditSeverity.LOW
        message = f"Data {action}: {resource} by user {user_id}"
        
        self.log_audit_event(
            event_type=event_type,
            message=message,
            severity=severity,
            outcome=outcome,
            user_id=user_id,
            resource=resource,
            ip_address=ip_address,
            additional_data=additional_details
        )
    
    def log_security_event(self,
                          event_type: AuditEventType,
                          message: str,
                          severity: AuditSeverity = AuditSeverity.HIGH,
                          ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None,
                          additional_details: Optional[Dict[str, Any]] = None):
        """Log security-related events"""
        
        self.log_audit_event(
            event_type=event_type,
            message=message,
            severity=severity,
            outcome=AuditOutcome.SUCCESS,  # Security events are generally "detected" successfully
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=additional_details
        )
    
    def log_admin_event(self,
                       admin_user_id: str,
                       action: str,
                       target: str,
                       outcome: AuditOutcome = AuditOutcome.SUCCESS,
                       ip_address: Optional[str] = None,
                       additional_details: Optional[Dict[str, Any]] = None):
        """Log administrative actions"""
        
        event_type_map = {
            "config_change": AuditEventType.ADMIN_CONFIG_CHANGE,
            "user_create": AuditEventType.ADMIN_USER_CREATE,
            "user_delete": AuditEventType.ADMIN_USER_DELETE,
            "backup": AuditEventType.ADMIN_BACKUP,
            "restore": AuditEventType.ADMIN_RESTORE
        }
        
        event_type = event_type_map.get(action.lower(), AuditEventType.ADMIN_CONFIG_CHANGE)
        message = f"Admin action: {action} on {target} by {admin_user_id}"
        
        self.log_audit_event(
            event_type=event_type,
            message=message,
            severity=AuditSeverity.HIGH,
            outcome=outcome,
            user_id=admin_user_id,
            resource=target,
            ip_address=ip_address,
            additional_data=additional_details
        )
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        
        uptime = datetime.now(timezone.utc) - self.start_time
        
        return {
            "session_id": self.session_id,
            "log_count": self.log_count,
            "uptime_seconds": uptime.total_seconds(),
            "sequence_number": self.sequence_number,
            "integrity_enabled": self.enable_integrity,
            "last_hash": self.last_hash[:16] + "..." if self.last_hash else None
        }


# Global audit logger instance
_audit_logger = None

def get_audit_logger(logger_name: str = "security_audit") -> SecurityAuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SecurityAuditLogger(logger_name)
    return _audit_logger

def initialize_audit_logging(enable_integrity: bool = True, 
                           enable_encryption: bool = False) -> SecurityAuditLogger:
    """Initialize the audit logging system"""
    global _audit_logger
    _audit_logger = SecurityAuditLogger(
        enable_integrity=enable_integrity,
        enable_encryption=enable_encryption
    )
    
    # Log initialization
    _audit_logger.log_audit_event(
        event_type=AuditEventType.SYSTEM_START,
        message="Audit logging system initialized",
        severity=AuditSeverity.LOW
    )
    
    return _audit_logger

# Convenience functions for common audit events
def audit_login_success(user_id: str, ip_address: str = None, user_agent: str = None):
    """Log successful login"""
    logger = get_audit_logger()
    logger.log_authentication_event(
        user_id=user_id,
        event_type=AuditEventType.LOGIN_SUCCESS,
        outcome=AuditOutcome.SUCCESS,
        ip_address=ip_address,
        user_agent=user_agent
    )

def audit_login_failure(user_id: str, ip_address: str = None, user_agent: str = None, reason: str = None):
    """Log failed login attempt"""
    logger = get_audit_logger()
    additional_data = {"failure_reason": reason} if reason else None
    logger.log_authentication_event(
        user_id=user_id,
        event_type=AuditEventType.LOGIN_FAILURE,
        outcome=AuditOutcome.FAILURE,
        ip_address=ip_address,
        user_agent=user_agent,
        additional_details=additional_data
    )

def audit_data_access(user_id: str, resource: str, action: str = "read", 
                     ip_address: str = None, outcome: AuditOutcome = AuditOutcome.SUCCESS):
    """Log data access"""
    logger = get_audit_logger()
    logger.log_data_event(
        user_id=user_id,
        action=action,
        resource=resource,
        outcome=outcome,
        ip_address=ip_address
    )

def audit_security_threat(threat_type: str, description: str, ip_address: str = None, 
                         user_agent: str = None, severity: AuditSeverity = AuditSeverity.HIGH):
    """Log security threat detection"""
    logger = get_audit_logger()
    logger.log_security_event(
        event_type=AuditEventType.SECURITY_THREAT_DETECTED,
        message=f"Security threat detected: {threat_type} - {description}",
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        additional_details={"threat_type": threat_type}
    )

def audit_admin_action(admin_user: str, action: str, target: str, 
                      ip_address: str = None, outcome: AuditOutcome = AuditOutcome.SUCCESS):
    """Log administrative action"""
    logger = get_audit_logger()
    logger.log_admin_event(
        admin_user_id=admin_user,
        action=action,
        target=target,
        outcome=outcome,
        ip_address=ip_address
    )
