from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response,
    Request,
    WebSocket,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt

from api.settings import settings
from api.schemas import TokenOut, TokenLoginOut, PasswordChangeIn
from api.models import User
from api.services.users import (
    create_user,
    get_user_by_username,
    verify_password,
    update_user_password,
)

router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_token(
    request: Request | None = None, websocket: WebSocket | None = None
) -> str:
    if request is not None:
        return await oauth2_scheme(request)
    token = websocket.query_params.get("token")
    if not token:
        auth = websocket.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(auth)
        if not auth or scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Not authenticated")
    return token


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


@router.post("/token", response_model=TokenLoginOut)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenLoginOut:
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user.username, "role": user.role})
    return TokenLoginOut(
        access_token=token,
        token_type="bearer",
        must_change_password=user.must_change_password,
    )


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenOut:
    if not settings.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Registration disabled"
        )
    if get_user_by_username(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )
    user = create_user(form_data.username, form_data.password)
    token = create_access_token({"sub": user.username, "role": user.role})
    return TokenOut(access_token=token, token_type="bearer")


async def get_current_user(token: str = Depends(get_token)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(username)
    if not user:
        raise credentials_exception
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordChangeIn, user: User = Depends(get_current_user)
) -> Response:
    update_user_password(user.id, payload.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
