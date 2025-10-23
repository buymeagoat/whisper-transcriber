#!/usr/bin/env python3
"""
T026 Security Hardening - Audit Logging Integration Examples
Shows how to integrate audit logging with existing application code.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/buymeagoat/dev/whisper-transcriber')

def create_audit_integration_examples():
    """Create examples showing audit logging integration"""
    
    print("🔗 T026 Security Hardening - Audit Logging Integration Examples")
    print("=" * 70)
    
    # Example 1: Basic audit logging demonstration
    demonstrate_basic_audit_logging()
    
    # Example 2: Authentication auditing
    demonstrate_authentication_auditing()
    
    # Example 3: Data operation auditing
    demonstrate_data_operation_auditing()
    
    # Example 4: Security event auditing
    demonstrate_security_event_auditing()
    
    # Example 5: Administrative action auditing
    demonstrate_admin_action_auditing()
    
    print("\\n" + "=" * 70)
    print("✅ Audit logging integration examples completed!")

def demonstrate_basic_audit_logging():
    """Demonstrate basic audit logging functionality"""
    print("\\n📝 Example 1: Basic Audit Logging")
    print("-" * 40)
    
    try:
        from api.audit.security_audit_logger import (
            get_audit_logger,
            AuditEventType,
            AuditSeverity,
            AuditOutcome,
            initialize_audit_logging
        )
        
        # Initialize audit logging
        audit_logger = initialize_audit_logging()
        
        # Log various types of events
        audit_logger.log_audit_event(
            event_type=AuditEventType.SYSTEM_START,
            message="Application started successfully",
            severity=AuditSeverity.LOW
        )
        
        audit_logger.log_audit_event(
            event_type=AuditEventType.DATA_READ,
            message="User accessed job listing",
            severity=AuditSeverity.LOW,
            user_id="demo_user",
            ip_address="192.168.1.100",
            resource="/api/jobs"
        )
        
        audit_logger.log_audit_event(
            event_type=AuditEventType.SECURITY_THREAT_DETECTED,
            message="Rate limit exceeded for IP address",
            severity=AuditSeverity.HIGH,
            ip_address="192.168.1.200",
            additional_data={"rate_limit": "100 requests/minute", "violations": 5}
        )
        
        # Get statistics
        stats = audit_logger.get_audit_statistics()
        
        print(f"   ✅ Logged {stats['log_count']} audit events")
        print(f"   📊 Session ID: {stats['session_id'][:8]}...")
        print(f"   🔒 Integrity enabled: {stats['integrity_enabled']}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demonstrate_authentication_auditing():
    """Demonstrate authentication event auditing"""
    print("\\n🔐 Example 2: Authentication Auditing")
    print("-" * 40)
    
    try:
        from api.audit.security_audit_logger import (
            audit_login_success,
            audit_login_failure,
            get_audit_logger,
            AuditEventType,
            AuditOutcome
        )
        
        # Simulate successful login
        audit_login_success(
            user_id="john_doe",
            ip_address="192.168.1.101",
            user_agent="Mozilla/5.0 (Chrome/91.0)"
        )
        
        # Simulate failed login attempts
        for i in range(3):
            audit_login_failure(
                user_id="attacker",
                ip_address="10.0.0.999",
                user_agent="curl/7.68.0",
                reason="Invalid password"
            )
        
        # Custom authentication event
        logger = get_audit_logger()
        logger.log_authentication_event(
            user_id="admin_user",
            event_type=AuditEventType.PASSWORD_CHANGE,
            outcome=AuditOutcome.SUCCESS,
            ip_address="192.168.1.102",
            additional_details={"password_strength": "strong", "previous_change": "30 days ago"}
        )
        
        print("   ✅ Logged authentication events")
        print("   🚨 Includes failed login attempts for threat detection")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demonstrate_data_operation_auditing():
    """Demonstrate data operation auditing"""
    print("\\n📊 Example 3: Data Operation Auditing")
    print("-" * 40)
    
    try:
        from api.audit.security_audit_logger import (
            audit_data_access,
            get_audit_logger,
            AuditEventType,
            AuditOutcome
        )
        
        # Simulate various data operations
        
        # File upload
        audit_data_access(
            user_id="content_creator",
            resource="audio_file.mp3",
            action="upload",
            ip_address="192.168.1.103"
        )
        
        # Data export (potentially sensitive)
        audit_data_access(
            user_id="analyst",
            resource="user_transcripts_export.zip",
            action="export",
            ip_address="192.168.1.104"
        )
        
        # Data deletion
        audit_data_access(
            user_id="admin",
            resource="job_id_12345",
            action="delete",
            ip_address="192.168.1.105"
        )
        
        # Failed data access
        audit_data_access(
            user_id="unauthorized_user",
            resource="confidential_document.txt",
            action="read",
            ip_address="10.0.0.999",
            outcome=AuditOutcome.FAILURE
        )
        
        print("   ✅ Logged data operation events")
        print("   📁 Includes uploads, exports, deletions, and access attempts")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demonstrate_security_event_auditing():
    """Demonstrate security event auditing"""
    print("\\n🛡️ Example 4: Security Event Auditing")
    print("-" * 40)
    
    try:
        from api.audit.security_audit_logger import (
            audit_security_threat,
            get_audit_logger,
            AuditEventType,
            AuditSeverity
        )
        
        logger = get_audit_logger()
        
        # Rate limiting violation
        audit_security_threat(
            threat_type="rate_limit_violation",
            description="IP exceeded 100 requests per minute limit",
            ip_address="10.0.0.999",
            severity=AuditSeverity.MEDIUM
        )
        
        # SQL injection attempt
        audit_security_threat(
            threat_type="sql_injection",
            description="Malicious SQL detected in search parameter",
            ip_address="192.168.1.200",
            user_agent="sqlmap/1.4.12",
            severity=AuditSeverity.HIGH
        )
        
        # File upload security violation
        logger.log_security_event(
            event_type=AuditEventType.SECURITY_BLOCKED_REQUEST,
            message="Blocked upload of executable file",
            severity=AuditSeverity.HIGH,
            ip_address="192.168.1.201",
            additional_details={
                "filename": "malware.exe",
                "content_type": "application/x-msdownload",
                "file_size": 1024000
            }
        )
        
        # Privilege escalation attempt
        logger.log_security_event(
            event_type=AuditEventType.SECURITY_THREAT_DETECTED,
            message="User attempted to access admin endpoint without authorization",
            severity=AuditSeverity.CRITICAL,
            ip_address="192.168.1.202",
            additional_details={
                "user_id": "regular_user",
                "attempted_endpoint": "/api/admin/users",
                "user_role": "standard"
            }
        )
        
        print("   ✅ Logged security threat events")
        print("   🚨 Includes rate limiting, injection attempts, and privilege escalation")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demonstrate_admin_action_auditing():
    """Demonstrate administrative action auditing"""
    print("\\n👑 Example 5: Administrative Action Auditing")
    print("-" * 40)
    
    try:
        from api.audit.security_audit_logger import (
            audit_admin_action,
            get_audit_logger,
            AuditEventType,
            AuditOutcome
        )
        
        # Configuration changes
        audit_admin_action(
            admin_user="system_admin",
            action="config_change",
            target="rate_limiting_settings",
            ip_address="192.168.1.10"
        )
        
        # User management
        audit_admin_action(
            admin_user="user_admin",
            action="user_create",
            target="new_employee_account",
            ip_address="192.168.1.11"
        )
        
        # System backup
        audit_admin_action(
            admin_user="backup_admin",
            action="backup",
            target="database_weekly_backup",
            ip_address="192.168.1.12"
        )
        
        # Failed admin action
        audit_admin_action(
            admin_user="junior_admin",
            action="user_delete",
            target="critical_system_account",
            ip_address="192.168.1.13",
            outcome=AuditOutcome.FAILURE
        )
        
        print("   ✅ Logged administrative action events")
        print("   🔧 Includes config changes, user management, and system operations")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def demonstrate_audit_analysis():
    """Demonstrate audit log analysis capabilities"""
    print("\\n📈 Example 6: Audit Log Analysis")
    print("-" * 40)
    
    try:
        from api.audit.log_analysis import analyze_audit_logs, get_security_alerts
        
        # Generate security report
        report = analyze_audit_logs(hours_back=1)
        
        print(f"   📊 Analysis Report:")
        print(f"     • Total events analyzed: {report.get('total_events_analyzed', 0)}")
        print(f"     • Alerts generated: {report.get('alerts_generated', 0)}")
        
        if 'security_score' in report:
            score_info = report['security_score']
            print(f"     • Security score: {score_info.get('grade', 'N/A')} ({score_info.get('score', 0)}/100)")
        
        if 'statistics' in report:
            stats = report['statistics']
            print(f"     • Unique users: {stats.get('unique_users', 0)}")
            print(f"     • Unique IPs: {stats.get('unique_ip_addresses', 0)}")
        
        # Get current alerts
        alerts = get_security_alerts(hours_back=1)
        if alerts:
            print(f"   🚨 Active Security Alerts:")
            for alert in alerts[:3]:  # Show first 3 alerts
                print(f"     • {alert.severity.upper()}: {alert.alert_type}")
                print(f"       {alert.message}")
        else:
            print("   ✅ No security alerts detected")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def show_audit_log_output():
    """Show actual audit log output"""
    print("\\n📄 Example 7: Audit Log Output")
    print("-" * 40)
    
    try:
        log_file = Path("logs/audit/security_audit.log")
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
            
            print(f"   📁 Audit log file: {log_file}")
            print(f"   📄 Total log entries: {len(lines)}")
            
            if lines:
                print("   📝 Sample log entries:")
                for i, line in enumerate(lines[-3:]):  # Show last 3 entries
                    try:
                        import json
                        entry = json.loads(line.strip())
                        timestamp = entry.get('timestamp', 'N/A')
                        event_type = entry.get('event_type', 'N/A')
                        severity = entry.get('severity', 'N/A')
                        message = entry.get('message', 'N/A')[:50] + "..." if len(entry.get('message', '')) > 50 else entry.get('message', 'N/A')
                        
                        print(f"     {i+1}. [{timestamp[:19]}] {severity.upper()} - {event_type}")
                        print(f"        {message}")
                    except:
                        print(f"     {i+1}. [Raw] {line.strip()[:100]}...")
        else:
            print("   📭 No audit log file found yet")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Main function to run audit logging examples"""
    
    # Ensure logs directory exists
    os.makedirs("logs/audit", exist_ok=True)
    
    create_audit_integration_examples()
    demonstrate_audit_analysis()
    show_audit_log_output()
    
    print("\\n" + "=" * 70)
    print("🎯 Integration Examples Summary:")
    print("   • Comprehensive audit logging system implemented")
    print("   • Input sanitization prevents log injection attacks")
    print("   • Structured JSON logging with integrity protection")
    print("   • Automated threat detection and security analysis")
    print("   • Integration with authentication, data ops, and admin actions")
    print("   • Real-time security monitoring and alerting")
    print("\\n📚 Next Steps:")
    print("   • Integrate audit middleware in main application")
    print("   • Add audit logging to all authentication endpoints")
    print("   • Set up automated security alert notifications")
    print("   • Configure log retention and archival policies")

if __name__ == "__main__":
    main()