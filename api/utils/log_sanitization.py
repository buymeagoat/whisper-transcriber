"""
Log Sanitization Utilities for T026 Security Hardening
Provides safe logging functions to prevent log injection attacks.
"""

import re
import html
import json
from typing import Any, Dict, List, Union, Optional
from datetime import datetime


class LogSanitizer:
    """
    Comprehensive log sanitization utility to prevent injection attacks.
    
    Features:
    - Input sanitization for log injection prevention
    - Structured logging support
    - Safe string formatting
    - Control character removal
    - Length limiting
    """
    
    def __init__(self, max_length: int = 1000):
        self.max_length = max_length
        self._setup_sanitization_patterns()
    
    def _setup_sanitization_patterns(self):
        """Setup regex patterns for sanitization"""
        
        # Dangerous patterns that could be used for log injection
        self.dangerous_patterns = [
            # Control characters including CRLF injection
            (r'[\r\n\f\t\v\x00-\x1f\x7f-\x9f]', ''),
            # Log4j-style variable substitution
            (r'\${[^}]*}', '[REMOVED]'),
            # Format string attacks
            (r'%[a-zA-Z0-9#\-\+\s]*[diouxXeEfFgGcs]', '[REMOVED]'),
            # Script tags
            (r'<script[^>]*>.*?</script>', '[SCRIPT_REMOVED]'),
            # JavaScript URLs
            (r'javascript:', '[JS_REMOVED]'),
            # Data URLs
            (r'data:.*?base64', '[DATA_URL_REMOVED]'),
            # LDAP injection patterns
            (r'\(.*?\)', '[LDAP_REMOVED]'),
            # SQL injection patterns
            (r'(union|select|insert|update|delete|drop|create|alter)\s+', '[SQL_REMOVED]'),
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE | re.DOTALL), replacement)
            for pattern, replacement in self.dangerous_patterns
        ]
    
    def sanitize_log_input(self, data: Any) -> str:
        """
        Sanitize input data for safe logging.
        
        Args:
            data: Input data to sanitize
            
        Returns:
            Sanitized string safe for logging
        """
        
        # Convert to string first
        if data is None:
            return "None"
        
        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, default=str, separators=(',', ':'))
            except (TypeError, ValueError):
                data_str = str(data)
        else:
            data_str = str(data)
        
        # Apply sanitization patterns
        sanitized = data_str
        for pattern, replacement in self.compiled_patterns:
            sanitized = pattern.sub(replacement, sanitized)
        
        # HTML escape for additional safety
        sanitized = html.escape(sanitized)
        
        # Remove any remaining control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Limit length to prevent log flooding
        if len(sanitized) > self.max_length:
            sanitized = sanitized[:self.max_length - 3] + "..."
        
        return sanitized
    
    def safe_format(self, template: str, *args, **kwargs) -> str:
        """
        Safe string formatting for logging.
        
        Args:
            template: Log message template
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Safely formatted log message
        """
        
        # Sanitize template
        safe_template = self.sanitize_log_input(template)
        
        # Sanitize arguments
        safe_args = [self.sanitize_log_input(arg) for arg in args]
        safe_kwargs = {k: self.sanitize_log_input(v) for k, v in kwargs.items()}
        
        try:
            # Use .format() instead of % formatting for safety
            return safe_template.format(*safe_args, **safe_kwargs)
        except (KeyError, ValueError, IndexError):
            # Fallback to template if formatting fails
            return safe_template
    
    def create_log_entry(self, level: str, message: str, **context) -> Dict[str, Any]:
        """
        Create a structured, safe log entry.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **context: Additional context data
            
        Returns:
            Structured log entry dictionary
        """
        
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'message': self.sanitize_log_input(message),
        }
        
        # Add sanitized context data
        if context:
            entry['context'] = {
                k: self.sanitize_log_input(v) for k, v in context.items()
            }
        
        return entry


# Global sanitizer instance
_log_sanitizer = LogSanitizer()


def safe_log_format(template: str, *args, **kwargs) -> str:
    """
    Safe log message formatting function.
    
    Usage:
        logger.info(safe_log_format("User {} logged in from {}", username, ip_address))
    """
    return _log_sanitizer.safe_format(template, *args, **kwargs)


def sanitize_for_log(data: Any) -> str:
    """
    Sanitize data for safe logging.
    
    Usage:
        logger.info(f"Processing file: {sanitize_for_log(filename)}")
    """
    return _log_sanitizer.sanitize_log_input(data)


def create_safe_log_entry(level: str, message: str, **context) -> str:
    """
    Create a safe, structured log entry as JSON string.
    
    Usage:
        logger.info(create_safe_log_entry("INFO", "User action", user_id=user_id, action=action))
    """
    entry = _log_sanitizer.create_log_entry(level, message, **context)
    return json.dumps(entry, separators=(',', ':'))


# Convenient wrapper functions for common logging patterns
def safe_user_log(message: str, user_id: str = None, ip_address: str = None, **kwargs) -> str:
    """Safe logging for user-related events"""
    context = {}
    if user_id:
        context['user_id'] = user_id
    if ip_address:
        context['ip_address'] = ip_address
    context.update(kwargs)
    
    return safe_log_format(message, **context)


def safe_error_log(message: str, error: Exception = None, **kwargs) -> str:
    """Safe logging for error events"""
    if error:
        kwargs['error_type'] = type(error).__name__
        kwargs['error_message'] = str(error)
    
    return safe_log_format(message, **kwargs)


def safe_security_log(message: str, threat_type: str = None, source_ip: str = None, **kwargs) -> str:
    """Safe logging for security events"""
    if threat_type:
        kwargs['threat_type'] = threat_type
    if source_ip:
        kwargs['source_ip'] = source_ip
    
    return safe_log_format(message, **kwargs)


# Migration helpers for updating existing logging statements
def migrate_format_string(original: str, *args) -> str:
    """
    Migrate % formatting to safe formatting.
    
    Usage:
        # Old: logger.info("User %s logged in" % username)
        # New: logger.info(migrate_format_string("User %s logged in", username))
    """
    # Replace % placeholders with {} placeholders
    safe_template = re.sub(r'%[sdf]', '{}', original)
    return safe_log_format(safe_template, *args)


def migrate_fstring(template: str, **kwargs) -> str:
    """
    Migrate f-strings to safe formatting.
    
    Usage:
        # Old: logger.info(f"User {username} from {ip}")
        # New: logger.info(migrate_fstring("User {username} from {ip}", username=username, ip=ip))
    """
    return safe_log_format(template, **kwargs)
