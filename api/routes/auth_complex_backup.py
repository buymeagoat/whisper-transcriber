"""Simplified auth routes for testing the /api/register endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.models import User
from api.orm_bootstrap import get_db

# Create router instance for /auth prefixed routes
router = APIRouter(prefix="/auth", tags=["authentication"])

# Create an API router for /api/auth prefixed routes
api_router = APIRouter(prefix="/api/auth", tags=["authentication", "api"])

# Create a direct API router for /api prefixed routes  
direct_api_router = APIRouter(prefix="/api", tags=["authentication", "direct-api"])

# Create a root router for direct endpoints
root_router = APIRouter(tags=["authentication"])

# Request models
class RegisterRequest(BaseModel):
    username: str
    password: str
    email: EmailStr

# Simple register endpoint for testing
@root_router.post("/api/register", response_model=dict)
async def api_register_user(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (Direct API endpoint for /api/register)."""
    try:
        # Simple user creation logic for testing
        user = User(
            username=register_data.username,
            email=register_data.email,
            hashed_password=f"hashed_{register_data.password}",  # Simple hash for testing
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "message": "User registered successfully", 
            "user_id": str(user.id),
            "username": user.username,
            "email": user.email
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Registration failed: {str(e)}"
        )

# Simple placeholder functions that might be expected
async def get_current_user():
    """Placeholder function."""
    pass

async def login():
    """Placeholder function."""
    pass
async def get_current_admin_user():
    """Placeholder function for admin user verification."""
    pass
