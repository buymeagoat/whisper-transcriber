"""
User management services for the Whisper Transcriber API.
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from api.orm_bootstrap import get_db
from api.models import User
from api.utils.logger import get_system_logger
from api.routes.auth import verify_token
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
            # Create default admin user
            admin_user = User(
                username="admin",
                hashed_password=hash_password("0AYw^lpZa!TM*iw0oIKX"),  # Strong generated password
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

async def get_current_user(current_user: dict = Depends(verify_token)) -> dict:
    """Get current authenticated user - wrapper for auth function."""
    # This function provides a service-level interface to the auth function
    # Import here to avoid circular imports
    from api.routes.auth import get_current_user as auth_get_current_user
    return await auth_get_current_user(current_user)

async def get_current_admin(current_user: dict = Depends(verify_token)) -> dict:
    """Get current authenticated admin user - wrapper for auth function."""
    # This function provides a service-level interface to the auth function  
    # Import here to avoid circular imports
    from api.routes.auth import get_current_admin_user
    return await get_current_admin_user(current_user)
