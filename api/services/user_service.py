"""Secure user management service for authentication system."""

import re
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import User
from ..orm_bootstrap import get_db
from ..settings import settings


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserService:
    """Secure user management service."""
    
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_EMAIL = "admin@admin.admin"

    def __init__(self):
        """Initialize user service with security validations."""
        self._validate_security_configuration()
    
    def _validate_security_configuration(self) -> None:
        """Validate that security configuration meets production standards."""
        # Skip validation in development/test environments to allow easier setup
        if hasattr(settings, 'environment') and settings.environment in ['development', 'test']:
            return
        
        if not settings.secret_key:
            raise ValueError(
                "SECRET_KEY must be set for production deployment. "
                "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        if len(settings.secret_key) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters long. "
                f"Current length: {len(settings.secret_key)}. "
                f"Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        # Check for common insecure values
        insecure_keys = [
            "",
            "secret",
            "password",
            "admin",
            "test",
            "development",
            "your-secret-key",
            "change-me",
            "default"
        ]
        
        if settings.secret_key.lower() in insecure_keys:
            raise ValueError(
                f"SECRET_KEY cannot be a common insecure value. "
                f"Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt with strong salt."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Generate salt with cost factor 12 (recommended for production)
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its bcrypt hash."""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception:
            # Never return True on error for security
            return False
    
    def create_user(
        self,
        db: Session,
        username: str,
        email: str,
        password: str,
        role: str = "user",
        must_change_password: bool = False
    ) -> User:
        """Create a new user with secure password hashing."""
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        if len(username.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")

        if not email or not email.strip():
            raise ValueError("Email cannot be empty")

        email_normalized = email.strip().lower()
        if not EMAIL_PATTERN.match(email_normalized):
            raise ValueError("Invalid email address")

        username_normalized = username.strip()
        
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter(func.lower(User.username) == username_normalized.lower())
            .first()
        )
        if existing_user:
            raise ValueError(f"User '{username}' already exists")

        existing_email = (
            db.query(User)
            .filter(func.lower(User.email) == email_normalized)
            .first()
        )
        if existing_email:
            raise ValueError(f"Email '{email_normalized}' is already in use")
        
        # Hash password securely
        hashed_password = self.hash_password(password)
        
        # Create new user
        user = User(
            username=username_normalized,
            email=email_normalized,
            hashed_password=hashed_password,
            role=role,
            must_change_password=must_change_password,
            created_at=datetime.utcnow()
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError as exc:
            db.rollback()
            detail = str(getattr(exc, "orig", exc)).lower()
            if "email" in detail:
                raise ValueError(f"Email '{email_normalized}' is already in use")
            raise ValueError(f"User '{username_normalized}' already exists")
    
    def authenticate_user(self, db: Session, username: str, password: str) -> User:
        """Authenticate a user with secure password verification."""
        if not username or not password:
            raise ValueError("Username and password are required")
        
        user = (
            db.query(User)
            .filter(func.lower(User.username) == username.strip().lower())
            .first()
        )
        if not user:
            raise ValueError("Invalid credentials")
        
        if not self.verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        
        return user
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        if not username:
            return None
        
        return (
            db.query(User)
            .filter(func.lower(User.username) == username.strip().lower())
            .first()
        )

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        if not email:
            return None

        return (
            db.query(User)
            .filter(func.lower(User.email) == email.strip().lower())
            .first()
        )
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    def update_password(
        self, 
        db: Session, 
        user_id: int, 
        new_password: str,
        clear_must_change: bool = True
    ) -> bool:
        """Update user password with secure hashing."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Hash new password
        hashed_password = self.hash_password(new_password)
        
        # Update user
        user.hashed_password = hashed_password
        if clear_must_change:
            user.must_change_password = False
        
        try:
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
    
    def change_password(
        self,
        db: Session,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> None:
        """Change user password after verifying current password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not self.verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Validate new password (leverage existing validation)
        self.hash_password(new_password)  # This will raise ValueError if invalid
        
        # Update password using existing method
        success = self.update_password(db, user_id, new_password)
        if not success:
            raise ValueError("Failed to update password")
    
    def ensure_admin_user_exists(self, db: Session) -> Dict[str, Any]:
        """Ensure an admin user exists, creating one if necessary."""
        # Check if any admin user exists
        admin_user = (
            db.query(User)
            .filter(func.lower(User.username) == self.DEFAULT_ADMIN_USERNAME)
            .first()
        )
        
        if admin_user:
            updated = False
            if not admin_user.email:
                admin_user.email = self.DEFAULT_ADMIN_EMAIL
                updated = True

            if admin_user.role != "admin":
                admin_user.role = "admin"
                updated = True

            if updated:
                try:
                    db.commit()
                except Exception:
                    db.rollback()

            return {
                "admin_exists": True,
                "action": "existing_admin_found",
                "username": admin_user.username,
                "email": admin_user.email,
                "created": False,
                "initial_setup": False
            }
        
        # No admin exists - this is first-run setup
        # Generate secure random password
        initial_password = secrets.token_urlsafe(16)  # 22 character secure password
        admin_username = self.DEFAULT_ADMIN_USERNAME
        
        try:
            admin_user = self.create_user(
                db=db,
                username=admin_username,
                email=self.DEFAULT_ADMIN_EMAIL,
                password=initial_password,
                role="admin",
                must_change_password=True  # Force password change on first login
            )
            
            return {
                "admin_exists": True,
                "action": "admin_created",
                "username": admin_username,
                "email": admin_user.email,
                "initial_password": initial_password,
                "created": True,
                "initial_setup": True,
                "message": (
                    f"Initial admin user created. "
                    f"Username: {admin_username}, "
                    f"Initial password: {initial_password} "
                    f"(MUST be changed on first login)"
                )
            }
        except Exception as e:
            return {
                "admin_exists": False,
                "action": "admin_creation_failed",
                "error": str(e),
                "created": False,
                "initial_setup": False
            }
    
    def is_first_run(self, db: Session) -> bool:
        """Check if this is the first run (no users exist)."""
        user_count = db.query(User).count()
        return user_count == 0


# Global user service instance
user_service = UserService()