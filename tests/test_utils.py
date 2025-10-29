"""
Test utilities for backward compatibility with legacy test files.
Provides functions that tests expect but don't exist in the updated codebase.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional
from api.services.user_service import user_service
from api.services.token_service import token_service
from api.settings import settings

# Legacy compatibility - redirect to new services
def hash_password(password: str) -> str:
    """Legacy compatibility for hash_password."""
    return user_service.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Legacy compatibility for verify_password."""
    return user_service.verify_password(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Legacy compatibility for create_access_token."""
    username = data.get("sub")
    if not username:
        raise ValueError("Token data must include 'sub' field with username")
    
    # Create user data dict for token service
    user_data = {
        "id": 1,
        "username": username,
        "role": "user"
    }
    
    return token_service.create_access_token(user_data, expires_delta)

def verify_token(token: str) -> Optional[str]:
    """Legacy compatibility for verify_token."""
    try:
        payload = token_service.verify_token(token)
        return payload.get("username")  # Return username, not user ID
    except Exception:
        return None

# Legacy compatibility constants
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"

# Legacy USERS_DB for tests that expect it
USERS_DB = {
    "testuser": {
        "username": "testuser",
        "password_hash": hash_password("testpassword123"),
        "role": "user",
        "is_admin": False,
        "created_at": datetime.utcnow()
    },
    "admin": {
        "username": "admin", 
        "password_hash": hash_password("admin123"),
        "role": "admin",
        "is_admin": True,
        "created_at": datetime.utcnow()
    }
}