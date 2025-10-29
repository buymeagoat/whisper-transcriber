"""Authentication routes for user login and token management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from ..models import User
from ..orm_bootstrap import get_db
from ..services.user_service import user_service
from ..services.token_service import token_service
from ..middlewares.session_security import session_security, secure_auth_required
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

# Create an API router for /api/auth prefixed routes (for frontend compatibility)
api_router = APIRouter(prefix="/api/auth", tags=["authentication", "api"])

# Create a direct API router for /api prefixed routes (for frontend direct API calls)
direct_api_router = APIRouter(prefix="/api", tags=["authentication", "direct-api"])

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

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserInfo(BaseModel):
    id: str
    username: str
    is_active: bool
    is_admin: bool = False
    roles: List[str] = []

class FirstRunSetupRequest(BaseModel):
    admin_password: str

class AdminSetupResponse(BaseModel):
    message: str
    initial_setup: bool
    username: Optional[str] = None
    initial_password: Optional[str] = None

# JWT settings - now using secure token service
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Default to 60 minutes


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token with comprehensive validation using secure session management."""
    try:
        # Extract token from secure storage (cookie or header)
        credentials = session_security.create_secure_credentials(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate session security (allow medium for API usage in development)
        security_check = session_security.validate_session_security(request)
        if security_check["security_level"] == "low":
            # In development environment, allow API usage with auth header
            is_development = settings.environment == "development"
            has_auth_header = security_check["checks"].get("has_auth_header", False)
            if not (is_development and has_auth_header):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Insufficient session security",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Extract and verify token
        user_data = token_service.extract_user_from_token(credentials.credentials)
        
        # Get user from database to ensure they still exist and are active
        user = user_service.get_user_by_id(db, int(user_data["id"]))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and ensure they have admin privileges."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest, 
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token with secure session management."""
    try:
        # Authenticate user with secure service
        user = user_service.authenticate_user(db, login_data.username, login_data.password)
        
        # Audit successful login
        audit_login_attempt(
            user_id=str(user.id),
            success=True,
            request=request
        )
        
        # Create secure access token
        user_data = {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
        access_token = token_service.create_access_token(user_data)
        
        # Set secure httpOnly cookies
        session_security.set_auth_cookies(response, access_token)
        
        # Also return token for API clients that can't use cookies
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except ValueError as e:
        # Audit failed login attempt
        audit_login_attempt(
            user_id=login_data.username,
            success=False,
            request=request,
            reason=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Audit unexpected error
        audit_login_attempt(
            user_id=login_data.username,
            success=False,
            request=request,
            reason=f"System error: {str(e)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error"
        )

# API router version for frontend compatibility
@api_router.post("/login", response_model=Token)
async def api_login(
    login_data: LoginRequest, 
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token with secure session management (API version)."""
    try:
        # Authenticate user with secure service
        user = user_service.authenticate_user(db, login_data.username, login_data.password)
        
        # Audit successful login
        audit_login_attempt(
            user_id=str(user.id),
            success=True,
            request=request
        )
        
        # Create secure access token
        user_data = {
            "id": user.id,
            "username": user.username,
            "role": user.role
        }
        access_token = token_service.create_access_token(user_data)
        
        # Set secure httpOnly cookies
        session_security.set_auth_cookies(response, access_token)
        
        # Also return token for API clients that can't use cookies
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except ValueError as e:
        # Audit failed login attempt
        audit_login_attempt(
            user_id=login_data.username,
            success=False,
            request=request,
            reason=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Audit unexpected error
        audit_login_attempt(
            user_id=login_data.username,
            success=False,
            request=request,
            reason=f"System error: {str(e)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error"
        )

# API router version for frontend compatibility
@api_router.post("/register", response_model=dict)
async def api_register_user(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (API version)."""
    try:
        user = user_service.create_user(
            db, 
            username=register_data.username, 
            password=register_data.password,
            role="user"
        )
        
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            "username": user.username
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

# API router version for getting current user info
@api_router.get("/me", response_model=UserInfo)
async def api_get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information (API version)."""
    return UserInfo(
        id=str(current_user.id),
        username=current_user.username,
        is_active=True,  # User is active if they can authenticate
        is_admin=(current_user.role == "admin"),
        roles=[current_user.role]
    )

# Direct API router version for frontend direct calls to /api/register
@direct_api_router.post("/register", response_model=dict)
async def direct_api_register_user(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (Direct API version for /api/register)."""
    try:
        user = user_service.create_user(
            db, 
            username=register_data.username, 
            password=register_data.password,
            role="user"
        )
        
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            "username": user.username
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserInfo(
        id=str(current_user.id),
        username=current_user.username,
        is_active=True,  # User is active if they can authenticate
        is_admin=(current_user.role == "admin"),
        roles=[current_user.role]
    )


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logout user and clear secure session cookies."""
    # Clear authentication cookies
    session_security.clear_auth_cookies(response)
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=Token)
async def refresh_token(response: Response, current_user: User = Depends(get_current_user)):
    """Refresh access token and update secure cookies."""
    # Create new secure access token
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }
    access_token = token_service.create_access_token(user_data)
    
    # Update secure cookies
    session_security.set_auth_cookies(response, access_token)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


# Root-level routes for compatibility with tests
@root_router.post("/token", response_model=Token)
async def get_token(
    login_data: LoginRequest, 
    request: Request, 
    response: Response,
    db: Session = Depends(get_db)
):
    """Root-level token endpoint for compatibility."""
    return await login(login_data, request, response, db)


@root_router.post("/register", response_model=dict)
async def register_user(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        user = user_service.create_user(
            db, 
            username=register_data.username, 
            password=register_data.password,
            role="user"
        )
        
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            "username": user.username
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


# Direct API endpoint for frontend calls to /api/register
@root_router.post("/api/register", response_model=dict) 
async def api_direct_register_user(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (Direct API endpoint for /api/register)."""
    try:
        user = user_service.create_user(
            db, 
            username=register_data.username, 
            password=register_data.password,
            role="user"
        )
        
        return {
            "message": "User registered successfully",
            "user_id": str(user.id),
            "username": user.username
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@root_router.post("/change-password", response_model=dict)
async def change_password(
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        user_service.change_password(
            db, 
            user_id=current_user.id,
            current_password=change_data.current_password,
            new_password=change_data.new_password
        )
        
        return {"message": "Password changed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )