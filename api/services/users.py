from __future__ import annotations

from datetime import datetime
from typing import Optional

from passlib.context import CryptContext

from api.models import User
from api.orm_bootstrap import SessionLocal
from api.utils.db_lock import db_lock

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(username: str, password: str, role: str = "user") -> User:
    """Create and persist a new user."""
    hashed = pwd_context.hash(password)
    with db_lock:
        with SessionLocal() as db:
            user = User(
                username=username,
                hashed_password=hashed,
                role=role,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user


def get_user_by_username(username: str) -> Optional[User]:
    """Return a User by username or None."""
    with SessionLocal() as db:
        return db.query(User).filter_by(username=username).first()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if password matches hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def list_users() -> list[User]:
    """Return all users."""
    with SessionLocal() as db:
        return db.query(User).order_by(User.id).all()


def update_user_role(user_id: int, role: str) -> Optional[User]:
    """Update a user's role and return the updated user or None."""
    with db_lock:
        with SessionLocal() as db:
            user = db.query(User).get(user_id)
            if not user:
                return None
            user.role = role
            db.commit()
            db.refresh(user)
            return user
