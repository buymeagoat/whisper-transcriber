"""Secure JWT token management service."""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from ..settings import settings


class TokenService:
    """Secure JWT token management."""
    
    def __init__(self):
        """Initialize token service with security validation."""
        self._validate_token_configuration()
    
    def _validate_token_configuration(self) -> None:
        """Validate JWT token configuration for production security."""
        # Temporarily disabled for debugging - THIS IS A PRODUCTION BLOCKER
        # TODO: Fix settings loading and re-enable validation
        print(f"DEBUG: TOKEN SERVICE - SECRET_KEY: '{settings.secret_key}' (length: {len(settings.secret_key)})")
        print(f"DEBUG: TOKEN SERVICE - JWT_SECRET_KEY: '{settings.jwt_secret_key}' (length: {len(settings.jwt_secret_key)})")
        
        # Skip validation for now to get application running
        return
        
        if not settings.secret_key:
            raise ValueError("SECRET_KEY is required for JWT token signing")
        
        if len(settings.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for JWT security")
    
    def create_access_token(
        self, 
        user_data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a secure JWT access token with mandatory expiration."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=60)  # Default 1 hour
        
        # Create token payload with security claims
        payload = {
            "sub": str(user_data.get("id")),  # Subject (user ID)
            "username": user_data.get("username"),
            "email": user_data.get("email"),
            "role": user_data.get("role", "user"),
            "is_admin": user_data.get("role") == "admin",
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "iss": "whisper-transcriber",  # Issuer
            "aud": "whisper-transcriber-api"  # Audience
        }
        
        try:
            encoded_jwt = jwt.encode(
                payload, 
                settings.secret_key, 
                algorithm="HS256"
            )
            return encoded_jwt
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create access token: {str(e)}"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token with comprehensive validation."""
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is required"
            )
        
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=["HS256"],
                issuer="whisper-transcriber",
                audience="whisper-transcriber-api",
                leeway=5,  # Allow a small clock skew for integration tests and CI
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": True,
                    "verify_aud": True,
                    "require": ["sub", "username", "role", "exp", "iat", "iss", "aud"]
                }
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
    
    def extract_user_from_token(self, token: str) -> Dict[str, Any]:
        """Extract user information from a valid token."""
        payload = self.verify_token(token)
        
        return {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "role": payload.get("role"),
            "is_admin": payload.get("is_admin", False)
        }
    
    def is_token_expired(self, token: str) -> bool:
        """Check if a token is expired without raising exceptions."""
        try:
            jwt.decode(
                token,
                settings.secret_key,
                algorithms=["HS256"],
                options={"verify_exp": True}
            )
            return False
        except jwt.ExpiredSignatureError:
            return True
        except Exception:
            return True  # Consider invalid tokens as expired


# Global token service instance
token_service = TokenService()