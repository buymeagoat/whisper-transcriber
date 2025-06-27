from __future__ import annotations

from typing import Dict

from api.models import UserSetting
from api.orm_bootstrap import SessionLocal
from api.app_state import db_lock


def get_settings(user_id: int) -> Dict[str, str]:
    """Return all settings for the given user as a dict."""
    with SessionLocal() as db:
        entries = db.query(UserSetting).filter_by(user_id=user_id).all()
        return {e.key: e.value for e in entries}


def update_settings(user_id: int, updates: Dict[str, str]) -> Dict[str, str]:
    """Update settings for a user and return the new values."""
    with db_lock:
        with SessionLocal() as db:
            existing = {
                e.key: e for e in db.query(UserSetting).filter_by(user_id=user_id).all()
            }
            for key, value in updates.items():
                entry = existing.get(key)
                if entry:
                    entry.value = value
                else:
                    entry = UserSetting(user_id=user_id, key=key, value=value)
                    db.add(entry)
            db.commit()
            entries = db.query(UserSetting).filter_by(user_id=user_id).all()
            return {e.key: e.value for e in entries}
