"""Authentication routes for user login and token management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
import hashlib
import secrets
from ..settings import settings

# T026 Security Hardening - Audit logging integration
from api.audit.integration import (
    audit_login_attempt,
    audit_administrative_action,
    extract_request_context
)
from api.audit.security_audit_logger import (
    AuditEventType,
    AuditSeverity,
    AuditOutcome
)

# Create router instance for /auth prefixed routes
router = APIRouter(prefix="/auth", tags=["authentication"])

# Create a second router for root-level routes that tests expect
root_router = APIRouter(tags=["authentication"])

# Security scheme
security = HTTPBearer()

# Response models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginRequest(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    id: str
    username: str
    is_active: bool
    is_admin: bool = False
    roles: List[str] = []

# Dummy user store (in production, this would be a database)
USERS_DB = {
    "admin": {
        "id": "1",
        "username": "admin",
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
        "is_active": True,
        "is_admin": True,
        "roles": ["admin", "user"]
    }
}

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Default to 60 minutes

def hash_password(password: str) -> str:
    """Hash a password using bcrypt for security."""
    import bcrypt
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    import bcrypt
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with mandatory expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default to 1 hour for security
        expire = datetime.utcnow() + timedelta(hours=1)
    
    # Always include expiration time
    to_encode.update({"exp": expire})
    # Add issued at time for additional security
    to_encode.update({"iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user info."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, request: Request):
    """Authenticate user and return access token."""
    user = USERS_DB.get(login_data.username)
    
    if not user or not verify_password(login_data.password, user["password_hash"]):
        # Audit failed login attempt
        audit_login_attempt(
            user_id=login_data.username,
            success=False,
            request=request,
            reason="Invalid credentials"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        # Audit failed login attempt for inactive user
        audit_login_attempt(
            user_id=login_data.username,
            success=False,
            request=request,
            reason="Inactive user account"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Audit successful login
    audit_login_attempt(
        user_id=login_data.username,
        success=True,
        request=request
    )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/me", response_model=UserInfo)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """Get current authenticated user information."""
    username = current_user["username"]
    user = USERS_DB.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserInfo(
        id=user["id"],
        username=user["username"],
        is_active=user["is_active"],
        is_admin=user.get("is_admin", False),
        roles=user.get("roles", [])
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """Logout user (client should discard token)."""
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: dict = Depends(verify_token)):
    """Refresh access token."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# Root-level routes for compatibility with tests
@root_router.post("/token", response_model=Token)
async def get_token(login_data: LoginRequest):
    """Root-level token endpoint for compatibility."""
    return await login(login_data)

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

@root_router.post("/register", response_model=dict)
async def register_user(register_data: RegisterRequest):
    """Register a new user."""
    if register_data.username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # In production, this would save to database
    new_user_id = str(len(USERS_DB) + 1)
    USERS_DB[register_data.username] = {
        "id": new_user_id,
        "username": register_data.username,
        "password_hash": hash_password(register_data.password),
        "is_active": True
    }
    
    return {
        "message": "User registered successfully",
        "user_id": new_user_id,
        "username": register_data.username
    }

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@root_router.post("/change-password", response_model=dict)
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: dict = Depends(verify_token)
):
    """Change user password."""
    username = current_user["username"]
    user = USERS_DB.get(username)
    
    if not user or not verify_password(change_data.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    USERS_DB[username]["password_hash"] = hash_password(change_data.new_password)
    
    return {"message": "Password changed successfully"}