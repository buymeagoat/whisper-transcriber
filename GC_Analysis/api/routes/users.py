from fastapi import APIRouter, Depends, HTTPException

from api.routes.auth import require_admin
from api.services.users import list_users, update_user_role
from api.schemas import UserListOut, UserOut, UserUpdateIn

router = APIRouter(prefix="/users")


@router.get("", response_model=UserListOut)
def get_users(user=Depends(require_admin)) -> UserListOut:
    users = list_users()
    return UserListOut(users=users)


@router.put("/{user_id}", response_model=UserOut)
def change_role(
    user_id: int, payload: UserUpdateIn, user=Depends(require_admin)
) -> UserOut:
    updated = update_user_role(user_id, payload.role)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated
