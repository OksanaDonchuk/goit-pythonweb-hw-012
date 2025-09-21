from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from src.conf import messages
from src.conf.config import settings


def create_email_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Створює JWT-токен для email-операцій (наприклад, підтвердження пошти або скидання паролю).

    Args:
        data (dict): Дані для кодування (наприклад, {"sub": email}).
        expires_delta (timedelta, optional): Час життя токена.
            Якщо не передано — використовується 7 днів.

    Returns:
        str: Згенерований JWT-токен.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=7))
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    """
    Декодує JWT-токен і отримує email користувача з payload.

    Args:
        token (str): JWT-токен, отриманий у листі.

    Returns:
        str: Email із поля ``sub``.

    Raises:
        HTTPException: Якщо токен недійсний або прострочений.
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
