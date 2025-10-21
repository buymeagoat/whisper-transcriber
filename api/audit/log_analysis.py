"""
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
