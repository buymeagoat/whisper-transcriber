"""
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
