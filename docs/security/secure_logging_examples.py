"""
T026 Security Hardening - Secure Logging Examples
Shows how to use secure logging patterns to prevent log injection.
"""

from api.utils.log_sanitization import (
    safe_log_format,
    sanitize_for_log,
    safe_user_log,
    safe_error_log,
    safe_security_log,
    migrate_format_string,
    migrate_fstring
)

# Example 1: Secure replacement for % formatting
def insecure_logging_example():
    """Examples of INSECURE logging patterns (DO NOT USE)"""
    
    username = "admin'; DROP TABLE users; --"
    error_msg = "\n\r\nFAKE LOG ENTRY: Admin logged in"
    
    # ❌ VULNERABLE: % string formatting
    # logger.info("User %s logged in" % username)
    
    # ❌ VULNERABLE: Direct f-string with user input  
    # logger.error(f"Error processing request: {error_msg}")
    
    # ❌ VULNERABLE: String concatenation
    # logger.warning("Failed login for user: " + username)
    
    # ❌ VULNERABLE: .format() with unsanitized input
    # logger.error("Exception occurred: {}".format(error_msg))

def secure_logging_examples():
    """Examples of SECURE logging patterns (USE THESE)"""
    
    username = "admin'; DROP TABLE users; --"
    error_msg = "\n\r\nFAKE LOG ENTRY: Admin logged in"
    user_id = "12345"
    ip_address = "192.168.1.100"
    
    # ✅ SECURE: Use safe_log_format for string formatting
    logger.info(safe_log_format("User {} logged in from IP {}", username, ip_address))
    
    # ✅ SECURE: Sanitize individual variables
    logger.error(f"Error processing request: {sanitize_for_log(error_msg)}")
    
    # ✅ SECURE: Use specialized logging functions
    safe_user_log("User login successful", user_id=user_id, ip_address=ip_address)
    
    # ✅ SECURE: Safe error logging
    try:
        # Some operation
        pass
    except Exception as e:
        logger.error(safe_error_log("Operation failed for user {}", error=e, user_id=user_id))
    
    # ✅ SECURE: Security event logging
    logger.warning(safe_security_log(
        "Suspicious activity detected", 
        threat_type="brute_force", 
        source_ip=ip_address
    ))

def migration_examples():
    """Examples of migrating existing logging statements"""
    
    username = "test_user"
    count = 42
    
    # Migrating % formatting
    # Old: logger.info("User %s has %d items" % (username, count))
    logger.info(migrate_format_string("User %s has %d items", username, count))
    
    # Migrating f-strings
    # Old: logger.info(f"User {username} has {count} items")
    logger.info(migrate_fstring("User {username} has {count} items", 
                               username=username, count=count))
    
    # Direct safe formatting
    logger.info(safe_log_format("User {} has {} items", username, count))

def authentication_logging_examples():
    """Secure logging for authentication events"""
    
    from api.audit.security_audit_logger import get_audit_logger
    
    # Use audit logger for security-sensitive events
    audit_logger = get_audit_logger()
    
    username = "john_doe"
    ip_address = "192.168.1.100"
    
    # Successful login
    audit_logger.log_authentication_event(
        user_id=sanitize_for_log(username),
        event_type=AuditEventType.LOGIN_SUCCESS,
        outcome=AuditOutcome.SUCCESS,
        ip_address=sanitize_for_log(ip_address)
    )
    
    # Failed login with reason
    reason = "Invalid password\n\rFake log entry"
    audit_logger.log_authentication_event(
        user_id=sanitize_for_log(username),
        event_type=AuditEventType.LOGIN_FAILURE,
        outcome=AuditOutcome.FAILURE,
        ip_address=sanitize_for_log(ip_address),
        additional_details={"reason": sanitize_for_log(reason)}
    )

def data_operation_logging_examples():
    """Secure logging for data operations"""
    
    user_id = "user123"
    filename = "../../etc/passwd\n\rFake log"
    file_size = 1024
    
    # File upload logging
    logger.info(safe_log_format(
        "File upload: User {} uploaded file {} ({} bytes)",
        user_id, filename, file_size
    ))
    
    # Data export logging (high security)
    export_data = {"sensitive": "data\n\rInjection attempt"}
    logger.warning(safe_log_format(
        "Data export: User {} exported {} records",
        user_id, len(export_data)
    ))
    # Note: Don't log the actual sensitive data content

def error_logging_examples():
    """Secure error and exception logging"""
    
    user_input = "'; DROP TABLE logs; --\n\rFake error"
    
    try:
        # Some operation that might fail
        raise ValueError(user_input)
    except Exception as e:
        # ✅ SECURE: Don't log user input directly
        logger.error(safe_error_log(
            "Validation failed for user input",
            error=e,
            input_length=len(user_input),
            user_id="user123"
        ))
        
        # ✅ SECURE: Log sanitized error details
        logger.error(safe_log_format(
            "Processing error: {}",
            sanitize_for_log(str(e))
        ))

def best_practices_summary():
    """
    Security Logging Best Practices Summary:
    
    1. NEVER use % string formatting with user input
    2. ALWAYS sanitize user input before logging
    3. USE safe_log_format() for dynamic content
    4. AVOID logging sensitive data (passwords, tokens, etc.)
    5. LIMIT log message length to prevent flooding
    6. VALIDATE and sanitize all external input
    7. USE structured logging with proper escaping
    8. IMPLEMENT audit logging for security events
    9. MONITOR logs for injection attempts
    10. REGULARLY scan for logging vulnerabilities
    
    Tools Available:
    - safe_log_format(): Safe string formatting
    - sanitize_for_log(): Input sanitization
    - safe_user_log(): User event logging
    - safe_error_log(): Error logging
    - safe_security_log(): Security event logging
    - Audit logger: Security-focused logging
    
    Migration Tools:
    - migrate_format_string(): Convert % formatting
    - migrate_fstring(): Convert f-strings
    """
    pass

if __name__ == "__main__":
    # This file provides examples and should not be executed directly
    print("This file contains secure logging examples.")
    print("Import the functions you need or copy the patterns.")
