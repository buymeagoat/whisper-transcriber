#!/usr/bin/env python3
"""
T026 Security Hardening - Comprehensive Audit Logging Implementation
Creates secure, structured audit logging for all security-sensitive operations.
"""

import os
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from enum import Enum

def create_audit_logging_system():
    """Create comprehensive audit logging system with security features"""
    
    # Audit Logger Implementation
    audit_logger_content = '''"""
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
        
        # Setup logging
        self._setup_logger(log_file)
        
        # Integrity protection
        self.session_id = str(uuid.uuid4())
        self.sequence_number = 0
        self.last_hash = self._calculate_initial_hash()
        
        # Sanitization patterns
        self._setup_sanitization_patterns()
        
        # Performance tracking
        self.log_count = 0
        self.start_time = datetime.now(timezone.utc)
    
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
            (r'[\\r\\n\\f\\t\\v\\x00-\\x1f\\x7f-\\x9f]', ''),  # Control characters
            (r'\\${[^}]*}', '[REMOVED]'),  # Variable substitution
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
'''

    # Audit Log Analysis Tools
    analysis_tools_content = '''"""
Audit Log Analysis and Monitoring Tools
Provides utilities for analyzing audit logs and detecting security patterns.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass

from api.config.security_validator import ConfigurationSecurityValidator


@dataclass
class SecurityAlert:
    """Represents a security alert from audit log analysis"""
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    details: Dict[str, Any]
    event_count: int = 1


class AuditLogAnalyzer:
    """
    Analyzes audit logs for security patterns and anomalies.
    
    Features:
    - Failed login detection
    - Privilege escalation monitoring
    - Data exfiltration patterns
    - Anomaly detection
    - Compliance reporting
    """
    
    def __init__(self, log_file_path: str = "logs/audit/security_audit.log"):
        self.log_file_path = Path(log_file_path)
        self.alerts = []
        
        # Analysis thresholds
        self.failed_login_threshold = 5  # Failed logins in time window
        self.time_window_minutes = 15
        self.data_access_threshold = 100  # Data accesses in time window
        
        # Pattern definitions
        self._setup_threat_patterns()
    
    def _setup_threat_patterns(self):
        """Setup patterns for threat detection"""
        
        self.threat_patterns = {
            "brute_force": {
                "event_types": ["auth.login.failure"],
                "threshold": 5,
                "time_window": 15,  # minutes
                "severity": "high"
            },
            "privilege_escalation": {
                "event_types": ["authz.privilege.escalation", "authz.role.change"],
                "threshold": 1,
                "time_window": 60,
                "severity": "critical"
            },
            "data_exfiltration": {
                "event_types": ["data.export", "data.read"],
                "threshold": 50,
                "time_window": 30,
                "severity": "high"
            },
            "admin_abuse": {
                "event_types": ["admin.user.delete", "admin.config.change"],
                "threshold": 3,
                "time_window": 60,
                "severity": "high"
            },
            "security_bypass": {
                "event_types": ["security.blocked_request"],
                "threshold": 10,
                "time_window": 10,
                "severity": "medium"
            }
        }
    
    def load_audit_logs(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """Load audit logs from the specified time period"""
        
        if not self.log_file_path.exists():
            return []
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        logs = []
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        log_entry = json.loads(line)
                        
                        # Parse timestamp
                        timestamp_str = log_entry.get('timestamp', '')
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            
                            # Only include logs within time window
                            if timestamp >= cutoff_time:
                                log_entry['parsed_timestamp'] = timestamp
                                logs.append(log_entry)
                    
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
        
        except FileNotFoundError:
            pass
        
        return sorted(logs, key=lambda x: x.get('parsed_timestamp', datetime.min.replace(tzinfo=timezone.utc)))
    
    def analyze_failed_logins(self, logs: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Analyze for brute force login attempts"""
        
        alerts = []
        
        # Group failed logins by IP and user
        failed_logins = defaultdict(lambda: defaultdict(list))
        
        for log in logs:
            if log.get('event_type') == 'auth.login.failure':
                ip = log.get('ip_address', 'unknown')
                user = log.get('user_id', 'unknown')
                timestamp = log.get('parsed_timestamp')
                
                if timestamp:
                    failed_logins[ip][user].append(timestamp)
        
        # Check for brute force patterns
        time_window = timedelta(minutes=self.time_window_minutes)
        
        for ip, users in failed_logins.items():
            for user, timestamps in users.items():
                # Check for failures within time window
                for i, start_time in enumerate(timestamps):
                    end_time = start_time + time_window
                    failures_in_window = [t for t in timestamps[i:] if t <= end_time]
                    
                    if len(failures_in_window) >= self.failed_login_threshold:
                        alerts.append(SecurityAlert(
                            alert_type="brute_force_login",
                            severity="high",
                            message=f"Brute force attack detected: {len(failures_in_window)} failed logins for user '{user}' from IP {ip}",
                            timestamp=start_time,
                            details={
                                "ip_address": ip,
                                "user_id": user,
                                "failure_count": len(failures_in_window),
                                "time_window_minutes": self.time_window_minutes
                            },
                            event_count=len(failures_in_window)
                        ))
                        break  # Only alert once per sequence
        
        return alerts
    
    def analyze_privilege_escalation(self, logs: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Analyze for privilege escalation attempts"""
        
        alerts = []
        
        escalation_events = [
            log for log in logs 
            if log.get('event_type') in ['authz.privilege.escalation', 'authz.role.change']
        ]
        
        for event in escalation_events:
            user_id = event.get('user_id', 'unknown')
            timestamp = event.get('parsed_timestamp')
            event_type = event.get('event_type')
            
            alerts.append(SecurityAlert(
                alert_type="privilege_escalation",
                severity="critical",
                message=f"Privilege escalation detected: {event_type} for user '{user_id}'",
                timestamp=timestamp,
                details={
                    "user_id": user_id,
                    "event_type": event_type,
                    "additional_data": event.get('additional_data', {})
                }
            ))
        
        return alerts
    
    def analyze_data_access_patterns(self, logs: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Analyze for unusual data access patterns"""
        
        alerts = []
        
        # Group data access events by user
        data_accesses = defaultdict(list)
        
        data_event_types = ['data.read', 'data.export', 'data.delete']
        
        for log in logs:
            if log.get('event_type') in data_event_types:
                user_id = log.get('user_id', 'unknown')
                timestamp = log.get('parsed_timestamp')
                
                if timestamp:
                    data_accesses[user_id].append({
                        'timestamp': timestamp,
                        'event_type': log.get('event_type'),
                        'resource': log.get('resource'),
                        'outcome': log.get('outcome')
                    })
        
        # Check for excessive data access
        time_window = timedelta(minutes=30)
        
        for user_id, accesses in data_accesses.items():
            for i, access in enumerate(accesses):
                start_time = access['timestamp']
                end_time = start_time + time_window
                
                accesses_in_window = [
                    a for a in accesses[i:] 
                    if a['timestamp'] <= end_time
                ]
                
                if len(accesses_in_window) >= self.data_access_threshold:
                    # Check for data export events (more suspicious)
                    export_events = [
                        a for a in accesses_in_window 
                        if a['event_type'] == 'data.export'
                    ]
                    
                    severity = "critical" if export_events else "high"
                    alert_type = "data_exfiltration" if export_events else "excessive_data_access"
                    
                    alerts.append(SecurityAlert(
                        alert_type=alert_type,
                        severity=severity,
                        message=f"Excessive data access: {len(accesses_in_window)} data operations by user '{user_id}' in 30 minutes",
                        timestamp=start_time,
                        details={
                            "user_id": user_id,
                            "access_count": len(accesses_in_window),
                            "export_count": len(export_events),
                            "time_window_minutes": 30
                        },
                        event_count=len(accesses_in_window)
                    ))
                    break
        
        return alerts
    
    def analyze_admin_activity(self, logs: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Analyze administrative activity for anomalies"""
        
        alerts = []
        
        # High-risk admin events
        high_risk_events = [
            'admin.user.delete',
            'admin.config.change',
            'admin.backup',
            'admin.restore'
        ]
        
        admin_events = [
            log for log in logs 
            if log.get('event_type', '').startswith('admin.')
        ]
        
        # Group by user and time
        admin_activity = defaultdict(list)
        
        for event in admin_events:
            user_id = event.get('user_id', 'unknown')
            timestamp = event.get('parsed_timestamp')
            
            if timestamp:
                admin_activity[user_id].append(event)
        
        # Check for excessive admin activity
        for user_id, events in admin_activity.items():
            high_risk_count = sum(
                1 for event in events 
                if event.get('event_type') in high_risk_events
            )
            
            if high_risk_count >= 3:
                alerts.append(SecurityAlert(
                    alert_type="excessive_admin_activity",
                    severity="high",
                    message=f"Excessive high-risk admin activity: {high_risk_count} actions by user '{user_id}'",
                    timestamp=events[0].get('parsed_timestamp'),
                    details={
                        "user_id": user_id,
                        "high_risk_count": high_risk_count,
                        "total_admin_events": len(events)
                    },
                    event_count=high_risk_count
                ))
        
        return alerts
    
    def analyze_security_events(self, logs: List[Dict[str, Any]]) -> List[SecurityAlert]:
        """Analyze security events for patterns"""
        
        alerts = []
        
        # Group security events by type and IP
        security_events = defaultdict(lambda: defaultdict(list))
        
        for log in logs:
            event_type = log.get('event_type', '')
            if event_type.startswith('security.'):
                ip = log.get('ip_address', 'unknown')
                timestamp = log.get('parsed_timestamp')
                
                if timestamp:
                    security_events[event_type][ip].append(timestamp)
        
        # Check for repeated security violations
        time_window = timedelta(minutes=10)
        
        for event_type, ips in security_events.items():
            for ip, timestamps in ips.items():
                if len(timestamps) >= 10:  # 10+ violations in any timeframe
                    alerts.append(SecurityAlert(
                        alert_type="repeated_security_violations",
                        severity="high",
                        message=f"Repeated security violations: {len(timestamps)} {event_type} events from IP {ip}",
                        timestamp=timestamps[0],
                        details={
                            "ip_address": ip,
                            "event_type": event_type,
                            "violation_count": len(timestamps)
                        },
                        event_count=len(timestamps)
                    ))
        
        return alerts
    
    def generate_security_report(self, hours_back: int = 24) -> Dict[str, Any]:
        """Generate comprehensive security analysis report"""
        
        logs = self.load_audit_logs(hours_back)
        
        if not logs:
            return {
                "status": "no_logs",
                "message": "No audit logs found for analysis",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Run all analyses
        alerts = []
        alerts.extend(self.analyze_failed_logins(logs))
        alerts.extend(self.analyze_privilege_escalation(logs))
        alerts.extend(self.analyze_data_access_patterns(logs))
        alerts.extend(self.analyze_admin_activity(logs))
        alerts.extend(self.analyze_security_events(logs))
        
        # Categorize alerts by severity
        severity_counts = Counter(alert.severity for alert in alerts)
        
        # Generate statistics
        event_types = Counter(log.get('event_type') for log in logs)
        unique_users = len(set(log.get('user_id') for log in logs if log.get('user_id')))
        unique_ips = len(set(log.get('ip_address') for log in logs if log.get('ip_address')))
        
        # Generate report
        report = {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "time_period_hours": hours_back,
            "total_events_analyzed": len(logs),
            "alerts_generated": len(alerts),
            "severity_breakdown": dict(severity_counts),
            "statistics": {
                "unique_users": unique_users,
                "unique_ip_addresses": unique_ips,
                "event_type_distribution": dict(event_types.most_common(10))
            },
            "alerts": [
                {
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat() if alert.timestamp else None,
                    "event_count": alert.event_count,
                    "details": alert.details
                }
                for alert in sorted(alerts, key=lambda x: (x.severity, x.timestamp), reverse=True)
            ]
        }
        
        # Add security score
        security_score = self._calculate_security_score(alerts, len(logs))
        report["security_score"] = security_score
        
        return report
    
    def _calculate_security_score(self, alerts: List[SecurityAlert], total_events: int) -> Dict[str, Any]:
        """Calculate overall security score based on alerts"""
        
        # Base score
        score = 100
        
        # Deduct points for alerts
        severity_penalties = {
            "critical": 25,
            "high": 10,
            "medium": 5,
            "low": 2
        }
        
        for alert in alerts:
            penalty = severity_penalties.get(alert.severity, 1)
            score -= penalty
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        # Determine grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": score,
            "grade": grade,
            "alert_count": len(alerts),
            "events_analyzed": total_events
        }


def analyze_audit_logs(hours_back: int = 24) -> Dict[str, Any]:
    """Convenience function to analyze audit logs"""
    analyzer = AuditLogAnalyzer()
    return analyzer.generate_security_report(hours_back)

def get_security_alerts(hours_back: int = 24) -> List[SecurityAlert]:
    """Get current security alerts"""
    analyzer = AuditLogAnalyzer()
    logs = analyzer.load_audit_logs(hours_back)
    
    alerts = []
    alerts.extend(analyzer.analyze_failed_logins(logs))
    alerts.extend(analyzer.analyze_privilege_escalation(logs))
    alerts.extend(analyzer.analyze_data_access_patterns(logs))
    alerts.extend(analyzer.analyze_admin_activity(logs))
    alerts.extend(analyzer.analyze_security_events(logs))
    
    return sorted(alerts, key=lambda x: (x.severity, x.timestamp), reverse=True)
'''

    # Write the audit logging files
    api_audit_dir = Path("api/audit")
    api_audit_dir.mkdir(exist_ok=True)
    
    # Write audit logger
    with open(api_audit_dir / "security_audit_logger.py", 'w') as f:
        f.write(audit_logger_content)
    print(f"Created audit logger: {api_audit_dir / 'security_audit_logger.py'}")
    
    # Write analysis tools
    with open(api_audit_dir / "log_analysis.py", 'w') as f:
        f.write(analysis_tools_content)
    print(f"Created analysis tools: {api_audit_dir / 'log_analysis.py'}")
    
    # Create __init__.py
    with open(api_audit_dir / "__init__.py", 'w') as f:
        f.write('"""Security audit logging package"""\\n')
    
    return api_audit_dir

def create_audit_middleware():
    """Create middleware to automatically audit HTTP requests"""
    
    middleware_content = '''"""
Audit Middleware for automatic request/response logging
"""

import time
import json
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from api.audit.security_audit_logger import (
    get_audit_logger,
    AuditEventType,
    AuditSeverity,
    AuditOutcome
)
from api.utils.logger import get_system_logger

logger = get_system_logger("audit_middleware")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit HTTP requests and responses.
    
    Features:
    - Automatic request/response logging
    - Security event detection
    - Performance monitoring
    - Selective auditing based on endpoints
    """
    
    def __init__(self, 
                 app,
                 audit_all_requests: bool = False,
                 audit_sensitive_endpoints: bool = True,
                 audit_failures: bool = True,
                 exclude_paths: Optional[list] = None):
        super().__init__(app)
        
        self.audit_all_requests = audit_all_requests
        self.audit_sensitive_endpoints = audit_sensitive_endpoints
        self.audit_failures = audit_failures
        self.exclude_paths = set(exclude_paths or ['/health', '/version', '/docs', '/openapi.json'])
        
        # Sensitive endpoints that should always be audited
        self.sensitive_endpoints = {
            '/api/auth/login',
            '/api/auth/logout',
            '/api/auth/register',
            '/api/auth/change-password',
            '/api/admin/',
            '/api/jobs/',
            '/api/users/',
            '/api/backup/',
            '/api/config/'
        }
        
        self.audit_logger = get_audit_logger()
    
    def _should_audit_request(self, request: Request) -> bool:
        """Determine if request should be audited"""
        
        path = request.url.path
        
        # Skip excluded paths
        if path in self.exclude_paths:
            return False
        
        # Always audit sensitive endpoints
        if self.audit_sensitive_endpoints:
            for sensitive_path in self.sensitive_endpoints:
                if path.startswith(sensitive_path):
                    return True
        
        # Audit all requests if configured
        if self.audit_all_requests:
            return True
        
        return False
    
    def _extract_user_context(self, request: Request) -> Dict[str, Optional[str]]:
        """Extract user context from request"""
        
        user_id = None
        session_id = None
        
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user'):
            user = getattr(request.state, 'user', None)
            if user:
                user_id = getattr(user, 'username', None) or getattr(user, 'id', None)
        
        # Try to get session from cookies or headers
        session_id = request.cookies.get('session_id') or request.headers.get('x-session-id')
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get('user-agent')
        }
    
    def _determine_event_type(self, request: Request, response: Response) -> AuditEventType:
        """Determine appropriate audit event type based on request"""
        
        path = request.url.path.lower()
        method = request.method.upper()
        
        # Authentication endpoints
        if '/auth/' in path:
            if 'login' in path:
                return AuditEventType.LOGIN_SUCCESS if response.status_code < 400 else AuditEventType.LOGIN_FAILURE
            elif 'logout' in path:
                return AuditEventType.LOGOUT
            elif 'register' in path:
                return AuditEventType.ADMIN_USER_CREATE
            elif 'password' in path:
                return AuditEventType.PASSWORD_CHANGE
        
        # Data operations
        if method == 'POST' and response.status_code < 400:
            return AuditEventType.DATA_CREATE
        elif method == 'GET':
            return AuditEventType.DATA_READ
        elif method in ['PUT', 'PATCH'] and response.status_code < 400:
            return AuditEventType.DATA_UPDATE
        elif method == 'DELETE' and response.status_code < 400:
            return AuditEventType.DATA_DELETE
        
        # Admin operations
        if '/admin/' in path:
            return AuditEventType.ADMIN_CONFIG_CHANGE
        
        # File operations
        if '/upload' in path or '/files/' in path:
            if method == 'POST':
                return AuditEventType.FILE_UPLOAD
            elif method == 'GET':
                return AuditEventType.FILE_DOWNLOAD
            elif method == 'DELETE':
                return AuditEventType.FILE_DELETE
        
        # Default to data read for GET, data create for others
        return AuditEventType.DATA_READ if method == 'GET' else AuditEventType.DATA_CREATE
    
    def _determine_severity(self, request: Request, response: Response) -> AuditSeverity:
        """Determine audit event severity"""
        
        path = request.url.path.lower()
        
        # High severity operations
        if any(keyword in path for keyword in ['/admin/', '/delete', '/backup', '/restore']):
            return AuditSeverity.HIGH
        
        # Medium severity for authentication
        if '/auth/' in path:
            return AuditSeverity.MEDIUM
        
        # High severity for failures
        if response.status_code >= 400:
            return AuditSeverity.HIGH if response.status_code >= 500 else AuditSeverity.MEDIUM
        
        return AuditSeverity.LOW
    
    def _get_additional_data(self, request: Request, response: Response, 
                           processing_time: float) -> Dict[str, Any]:
        """Get additional data for audit log"""
        
        data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "content_length": response.headers.get("content-length"),
            "referer": request.headers.get("referer")
        }
        
        # Add request body size for uploads
        if request.headers.get("content-length"):
            data["request_size"] = request.headers.get("content-length")
        
        # Add error details for failures
        if response.status_code >= 400:
            data["error_status"] = response.status_code
        
        return data
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and audit if needed"""
        
        # Check if we should audit this request
        should_audit = self._should_audit_request(request)
        
        # Record start time for performance tracking
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Audit if needed
            if should_audit or (self.audit_failures and response.status_code >= 400):
                await self._audit_request(request, response, processing_time)
            
            return response
        
        except Exception as e:
            # Create error response for auditing
            processing_time = time.time() - start_time
            
            # Create a mock response for auditing
            error_response = Response(status_code=500)
            
            # Always audit exceptions
            await self._audit_request(request, error_response, processing_time, exception=str(e))
            
            # Re-raise the exception
            raise
    
    async def _audit_request(self, request: Request, response: Response, 
                           processing_time: float, exception: Optional[str] = None):
        """Audit the request/response"""
        
        try:
            # Extract user context
            user_context = self._extract_user_context(request)
            
            # Determine event details
            event_type = self._determine_event_type(request, response)
            severity = self._determine_severity(request, response)
            outcome = AuditOutcome.FAILURE if response.status_code >= 400 or exception else AuditOutcome.SUCCESS
            
            # Create message
            if exception:
                message = f"Request exception: {request.method} {request.url.path} - {exception}"
            else:
                message = f"Request: {request.method} {request.url.path} - {response.status_code}"
            
            # Get additional data
            additional_data = self._get_additional_data(request, response, processing_time)
            if exception:
                additional_data["exception"] = exception
            
            # Log audit event
            self.audit_logger.log_audit_event(
                event_type=event_type,
                message=message,
                severity=severity,
                outcome=outcome,
                user_id=user_context["user_id"],
                session_id=user_context["session_id"],
                ip_address=user_context["ip_address"],
                user_agent=user_context["user_agent"],
                resource=request.url.path,
                additional_data=additional_data
            )
        
        except Exception as audit_error:
            # Never let audit failures break the application
            logger.error(f"Failed to audit request: {audit_error}")
'''

    # Write audit middleware
    with open(Path("api/middlewares/audit_middleware.py"), 'w') as f:
        f.write(middleware_content)
    print(f"Created audit middleware: api/middlewares/audit_middleware.py")

def create_audit_integration():
    """Create integration helper for existing code"""
    
    integration_content = '''"""
Integration helper for adding audit logging to existing code
"""

import functools
from typing import Callable, Any, Optional, Dict
from fastapi import Request

from api.audit.security_audit_logger import (
    get_audit_logger,
    AuditEventType,
    AuditSeverity,
    AuditOutcome,
    audit_login_success,
    audit_login_failure,
    audit_data_access,
    audit_security_threat,
    audit_admin_action
)


def audit_function_call(event_type: AuditEventType, 
                       severity: AuditSeverity = AuditSeverity.MEDIUM,
                       resource: Optional[str] = None):
    """Decorator to automatically audit function calls"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            
            try:
                result = await func(*args, **kwargs)
                
                # Log successful operation
                audit_logger.log_audit_event(
                    event_type=event_type,
                    message=f"Function call successful: {func.__name__}",
                    severity=severity,
                    outcome=AuditOutcome.SUCCESS,
                    resource=resource or func.__name__,
                    additional_data={"function": func.__name__, "args_count": len(args)}
                )
                
                return result
            
            except Exception as e:
                # Log failed operation
                audit_logger.log_audit_event(
                    event_type=event_type,
                    message=f"Function call failed: {func.__name__} - {str(e)}",
                    severity=AuditSeverity.HIGH,
                    outcome=AuditOutcome.FAILURE,
                    resource=resource or func.__name__,
                    additional_data={"function": func.__name__, "error": str(e)}
                )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            audit_logger = get_audit_logger()
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful operation
                audit_logger.log_audit_event(
                    event_type=event_type,
                    message=f"Function call successful: {func.__name__}",
                    severity=severity,
                    outcome=AuditOutcome.SUCCESS,
                    resource=resource or func.__name__,
                    additional_data={"function": func.__name__, "args_count": len(args)}
                )
                
                return result
            
            except Exception as e:
                # Log failed operation
                audit_logger.log_audit_event(
                    event_type=event_type,
                    message=f"Function call failed: {func.__name__} - {str(e)}",
                    severity=AuditSeverity.HIGH,
                    outcome=AuditOutcome.FAILURE,
                    resource=resource or func.__name__,
                    additional_data={"function": func.__name__, "error": str(e)}
                )
                
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def extract_request_context(request: Request) -> Dict[str, Optional[str]]:
    """Extract audit context from FastAPI request"""
    
    user_id = None
    if hasattr(request.state, 'user'):
        user = getattr(request.state, 'user', None)
        if user:
            user_id = getattr(user, 'username', None) or getattr(user, 'id', None)
    
    return {
        "user_id": user_id,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get('user-agent'),
        "session_id": request.cookies.get('session_id')
    }


# Convenience functions for common audit scenarios
def audit_login_attempt(user_id: str, success: bool, request: Request, reason: Optional[str] = None):
    """Audit login attempt"""
    context = extract_request_context(request)
    
    if success:
        audit_login_success(
            user_id=user_id,
            ip_address=context["ip_address"],
            user_agent=context["user_agent"]
        )
    else:
        audit_login_failure(
            user_id=user_id,
            ip_address=context["ip_address"],
            user_agent=context["user_agent"],
            reason=reason
        )


def audit_data_operation(user_id: str, action: str, resource: str, 
                        request: Request, success: bool = True):
    """Audit data operation"""
    context = extract_request_context(request)
    outcome = AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE
    
    audit_data_access(
        user_id=user_id,
        resource=resource,
        action=action,
        ip_address=context["ip_address"],
        outcome=outcome
    )


def audit_security_event(threat_type: str, description: str, request: Request, 
                        severity: AuditSeverity = AuditSeverity.HIGH):
    """Audit security event"""
    context = extract_request_context(request)
    
    audit_security_threat(
        threat_type=threat_type,
        description=description,
        ip_address=context["ip_address"],
        user_agent=context["user_agent"],
        severity=severity
    )


def audit_administrative_action(admin_user: str, action: str, target: str, 
                               request: Request, success: bool = True):
    """Audit administrative action"""
    context = extract_request_context(request)
    outcome = AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE
    
    audit_admin_action(
        admin_user=admin_user,
        action=action,
        target=target,
        ip_address=context["ip_address"],
        outcome=outcome
    )
'''

    # Write integration helper
    with open(Path("api/audit/integration.py"), 'w') as f:
        f.write(integration_content)
    print(f"Created audit integration: api/audit/integration.py")

def main():
    """Main function to implement comprehensive audit logging"""
    
    print("🔒 T026 Security Hardening - Comprehensive Audit Logging Implementation")
    print("=" * 70)
    
    # Create audit logging system
    audit_dir = create_audit_logging_system()
    print(f"✅ Created audit logging system in {audit_dir}")
    
    # Create audit middleware
    create_audit_middleware()
    print("✅ Created audit middleware for automatic request logging")
    
    # Create integration helpers
    create_audit_integration()
    print("✅ Created audit integration helpers")
    
    # Create logs directory structure
    logs_dir = Path("logs/audit")
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created audit logs directory: {logs_dir}")
    
    print("\\n" + "=" * 70)
    print("✅ Comprehensive audit logging implementation completed!")
    print("\\n📋 Components created:")
    print("   • Security audit logger with input sanitization")
    print("   • Audit log analysis and monitoring tools")
    print("   • Automatic audit middleware for HTTP requests")
    print("   • Integration helpers for existing code")
    print("   • Structured JSON logging with integrity protection")
    print("\\n🔧 Features implemented:")
    print("   • Input sanitization to prevent log injection")
    print("   • Structured audit events with standardized types")
    print("   • Integrity protection with hash chaining")
    print("   • Automatic security threat detection")
    print("   • Performance monitoring and statistics")
    print("   • Compliance-ready audit trails")

if __name__ == "__main__":
    main()