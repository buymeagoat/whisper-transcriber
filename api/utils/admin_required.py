"""
Admin access control utilities.
"""

from functools import wraps
from fastapi import HTTPException, status, Depends
from typing import Callable, Any

def admin_required(func: Callable) -> Callable:
    """
    Decorator to require admin access for endpoint functions.
    
    Args:
        func: The endpoint function to wrap
        
    Returns:
        Wrapped function that checks admin access
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Get current_user from kwargs (it should be passed as a dependency)
        current_user = kwargs.get("current_user")
        if current_user and not current_user.get("is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return await func(*args, **kwargs)
    return wrapper

async def check_admin_required(current_user: dict) -> None:
    """
    Function to check if the current user has admin access.
    
    Args:
        current_user: Dictionary containing user information
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )