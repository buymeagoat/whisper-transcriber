from __future__ import annotations

from typing import Optional

from api.models import ConfigEntry
from api.orm_bootstrap import SessionLocal
from api.app_state import db_lock


def get_value(key: str) -> Optional[str]:
    with SessionLocal() as db:
        entry = db.query(ConfigEntry).filter_by(key=key).first()
        return entry.value if entry else None


def set_value(key: str, value: str) -> None:
    with db_lock:
        with SessionLocal() as db:
            entry = db.query(ConfigEntry).filter_by(key=key).first()
            if entry:
                entry.value = value
            else:
                entry = ConfigEntry(key=key, value=value)
                db.add(entry)
            db.commit()


def get_cleanup_config(default_enabled: bool, default_days: int) -> dict:
    enabled = get_value("cleanup_enabled")
    days = get_value("cleanup_days")
    return {
        "cleanup_enabled": default_enabled if enabled is None else enabled == "1",
        "cleanup_days": default_days if days is None else int(days),
    }


def update_cleanup_config(
    enabled: Optional[bool],
    days: Optional[int],
    *,
    default_enabled: bool,
    default_days: int,
) -> dict:
    if enabled is not None:
        set_value("cleanup_enabled", "1" if enabled else "0")
        default_enabled = enabled
    if days is not None:
        set_value("cleanup_days", str(days))
        default_days = days
    return {
        "cleanup_enabled": default_enabled,
        "cleanup_days": default_days,
    }
