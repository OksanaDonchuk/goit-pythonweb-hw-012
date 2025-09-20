from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from src.conf import messages
from src.conf.config import settings


def create_email_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Створює JWT токен для email операцій (підтвердження/скидання паролю).

    Args:
        data (dict): Дані для кодування (наприклад {"sub": email}).
        expires_delta (timedelta, optional): Час життя токена.
            Якщо не передано — використовується 7 днів.

    Returns:
        str: JWT токен
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    """
    Декодує JWT токен та отримує email користувача.

    Args:
        token (str): JWT токен

    Returns:
        str: Email з поля "sub"

    Raises:
        HTTPException: Якщо токен недійсний.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=messages.invalid_token,
        )
