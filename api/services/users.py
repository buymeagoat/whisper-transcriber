from __future__ import annotations

from datetime import datetime
from typing import Optional

from passlib.context import CryptContext

from api.models import User
from api.orm_bootstrap import SessionLocal
from api.app_state import db_lock

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(username: str, password: str) -> User:
    """Create and persist a new user."""
    hashed = pwd_context.hash(password)
    with db_lock:
        with SessionLocal() as db:
            user = User(
                username=username, hashed_password=hashed, created_at=datetime.utcnow()
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
