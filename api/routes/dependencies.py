"""Shared FastAPI dependencies for route modules."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from api.middlewares.session_security import session_security
from api.orm_bootstrap import get_db
from api.services.token_service import token_service
from api.services.user_service import user_service


async def get_authenticated_user_id(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
    db: Session = Depends(get_db),
) -> str:
    """Resolve the authenticated caller's user identifier.

    Favors the JWT carried via secure cookies or the Authorization header and
    falls back to the legacy ``X-User-ID`` header for compatibility with older
    integrations.
    """

    if x_user_id:
        return x_user_id

    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        credentials = session_security.create_secure_credentials(request)
        if credentials:
            token = credentials.credentials

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_payload = token_service.extract_user_from_token(token)
    except HTTPException as exc:  # Propagate standard auth errors
        raise exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    user_id = user_payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    user = user_service.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return str(user.id)
