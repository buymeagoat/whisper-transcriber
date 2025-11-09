"""Shared FastAPI dependencies for route modules."""
from fastapi import Header, HTTPException


async def get_authenticated_user_id(x_user_id: str | None = Header(default=None, alias="X-User-ID")) -> str:
    """Return the caller's user identifier from the ``X-User-ID`` header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID header")
    return x_user_id
