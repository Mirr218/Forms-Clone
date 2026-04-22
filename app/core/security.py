from datetime import datetime, timedelta, timezone
from typing import Any, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext

from app.core.config import security_config

JWT_COOKIE_KEY = "access_token"


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=security_config.jwt_expire_minutes
    )

    # Создаем данные для JWT
    to_encode = {"exp": expire, "sub": str(subject)}

    # Кодируем JWT
    encoded_jwt = jwt.encode(
        to_encode,
        security_config.jwt_secret_key,
        algorithm=security_config.jwt_algorithm,
    )

    return encoded_jwt


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
    )

    try:
        # Декодируем JWT
        payload = jwt.decode(
            token,
            security_config.jwt_secret_key,
            algorithms=[security_config.jwt_algorithm],
        )

        # Получаем ID пользователя
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
        return int(user_id)
    except Exception:
        raise credentials_exception
