from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from api import config

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

hashed_password = pwd_context.hash(config.AUTH_PASSWORD)


def verify_password(plain_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != config.AUTH_USERNAME or not verify_password(
        form_data.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": config.AUTH_USERNAME})
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username != config.AUTH_USERNAME:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username
