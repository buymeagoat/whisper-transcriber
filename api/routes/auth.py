"""Authentication routes for single-admin login and token management."""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr
from typing import List
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

# Root-level routes maintained for backwards compatibility with tests and scripts
root_router = APIRouter(tags=["authentication"])


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
    email: EmailStr
    is_active: bool
    is_admin: bool = False
    roles: List[str] = []

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
        
        # Validate session security requirements for API usage
        security_check = session_security.validate_session_security(request)
        if security_check["security_level"] == "low":
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
    """Authenticate the single admin user and return an access token."""
    supplied_username = (login_data.username or "admin").strip().lower()

    if not settings.multi_user_mode_enabled and supplied_username != "admin":
        audit_login_attempt(
            user_id=supplied_username,
            success=False,
            request=request,
            reason="Single-user mode: admin account only"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    target_username = supplied_username if settings.multi_user_mode_enabled else "admin"

    try:
        user = user_service.authenticate_user(db, target_username, login_data.password)

        audit_login_attempt(
            user_id=str(user.id),
            success=True,
            request=request
        )

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
        access_token = token_service.create_access_token(user_data)

        session_security.set_auth_cookies(response, access_token)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    except ValueError as exc:
        audit_login_attempt(
            user_id="admin",
            success=False,
            request=request,
            reason=str(exc)
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:  # pragma: no cover - defensive
        audit_login_attempt(
            user_id="admin",
            success=False,
            request=request,
            reason=f"System error: {str(exc)}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error"
        )

@api_router.get("/me", response_model=UserInfo)
async def api_get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information (API version)."""
    return UserInfo(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        is_active=True,
        is_admin=(current_user.role == "admin"),
        roles=[current_user.role]
    )

# API router version for getting current user info
@api_router.post("/login", response_model=Token)
async def api_login(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    return await login(login_data, request, response, db)

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserInfo(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
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
        "email": current_user.email,
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