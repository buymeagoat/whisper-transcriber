"""
User management services for the Whisper Transcriber API.
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from api.orm_bootstrap import get_db
from api.models import User
from api.utils.logger import get_system_logger
# Note: Removed circular import to avoid startup issues
# from api.routes.auth import get_current_user as auth_get_current_user
import bcrypt

logger = get_system_logger("users")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt for security."""
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def ensure_default_admin():
    """Ensure a default admin user exists."""
    try:
        # Get a database session
        db = next(get_db())
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # Create default admin user with simple password for development
            admin_user = User(
                username="admin",
                hashed_password=hash_password("admin123"),  # Simple default password
                role="admin",
                must_change_password=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created default admin user (username: admin, password: admin123)")
        else:
            logger.info("Admin user already exists")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Failed to ensure default admin user: {e}")

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_user(db: Session, username: str, password: str, role: str = "user") -> User:
    """Create a new user."""
    user = User(
        username=username,
        hashed_password=hash_password(password),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

async def get_current_user(token_data: dict) -> dict:
    """Get current authenticated user - wrapper for auth function."""
    # Note: This function has been simplified to avoid circular imports
    # The actual authentication logic is in api.routes.auth.get_current_user
    # Use FastAPI Depends() directly on that function instead
    return token_data

async def get_current_admin(current_user) -> User:
    """Get current authenticated admin user - wrapper for auth function."""
    # Note: This function has been simplified to avoid circular imports
    # The actual authentication logic is in api.routes.auth.get_current_admin_user
    # Use FastAPI Depends() directly on that function instead
    if current_user.role != "admin":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
