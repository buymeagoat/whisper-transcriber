from fastapi import APIRouter, Depends

from api.routes.auth import get_current_user
from api.models import User
from api.schemas import UserSettingsOut, UserSettingsIn
from api.services import user_settings as service

router = APIRouter(prefix="/user")


@router.get("/settings", response_model=UserSettingsOut)
def get_settings(user: User = Depends(get_current_user)) -> UserSettingsOut:
    values = service.get_settings(user.id)
    return UserSettingsOut(default_model=values.get("default_model"))


@router.post("/settings", response_model=UserSettingsOut)
def update_settings(
    payload: UserSettingsIn, user: User = Depends(get_current_user)
) -> UserSettingsOut:
    updates = {}
    if payload.default_model is not None:
        updates["default_model"] = payload.default_model
    values = service.update_settings(user.id, updates)
    return UserSettingsOut(default_model=values.get("default_model"))
