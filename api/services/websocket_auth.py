"""
WebSocket Authentication Helper for Enhanced WebSocket Service
Provides authentication utilities specifically for WebSocket connections.
"""

import jwt
from typing import Optional
from datetime import datetime
from fastapi import HTTPException

from api.routes.auth import USERS_DB, verify_password
from api.models import User
from api.settings import settings
from api.utils.logger import get_system_logger

logger = get_system_logger("websocket_auth")

class AuthenticationError(Exception):
    """Custom authentication error for WebSocket connections."""
    pass

def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        # Use the same secret key as the main auth system
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        
        # Check token expiration
        exp_timestamp = payload.get("exp")
        if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
            raise AuthenticationError("Token expired")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"Token verification failed: {str(e)}")

async def get_current_user_websocket(token: str) -> Optional[User]:
    """Get current user from WebSocket token."""
    try:
        # Verify the JWT token
        payload = verify_jwt_token(token)
        username = payload.get("sub")
        
        if not username:
            raise AuthenticationError("Token missing username")
        
        # Get user from database (using the dummy store for now)
        user_data = USERS_DB.get(username)
        if not user_data:
            raise AuthenticationError("User not found")
        
        if not user_data.get("is_active", False):
            raise AuthenticationError("User account disabled")
        
        # Create user object (simulating database user)
        user = User(
            id=int(user_data["id"]),
            username=user_data["username"],
            email=f"{username}@example.com",  # Default email
            hashed_password=user_data["password_hash"],
            role="admin" if user_data.get("is_admin", False) else "user",
            is_active=user_data.get("is_active", True)
        )
        
        return user
        
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        raise AuthenticationError(f"Authentication failed: {str(e)}")

def requires_admin_role_websocket(user: User) -> bool:
    """Check if user has admin role for WebSocket connections."""
    return user.role == "admin"

def requires_user_access_websocket(user: User, resource_user_id: int) -> bool:
    """Check if user has access to a specific resource."""
    return user.id == resource_user_id or user.role == "admin"
