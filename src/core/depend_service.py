from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.services.auth_services import AuthService, oauth2_scheme
from src.services.user_services import UserService
from src.entity.models import User, UserRole
from src.database.db import get_db


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """
    Повертає сервіс для роботи з автентифікацією.

    Args:
        db (AsyncSession): Сесія бази даних (DI через Depends).

    Returns:
        AuthService: Сервіс авторизації та управління токенами.
    """
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)):
    """
    Повертає сервіс для роботи з користувачами.

    Args:
        db (AsyncSession): Сесія бази даних (DI через Depends).

    Returns:
        UserService: Сервіс із бізнес-логікою над користувачами.
    """
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Отримує поточного користувача на основі access-токена.

    Args:
        token (str): JWT access-токен (DI через Depends).
        auth_service (AuthService): Сервіс для роботи з токенами.

    Raises:
        HTTPException(401): Якщо токен невалідний або користувача не знайдено.

    Returns:
        User: Поточний автентифікований користувач.
    """
    return await auth_service.get_current_user(token)


def get_current_moderator_user(current_user: User = Depends(get_current_user)):
    """
    Перевіряє, що користувач має роль MODERATOR або ADMIN.

    Args:
        current_user (User): Поточний користувач (DI через Depends).

    Raises:
        HTTPException(403): Якщо користувач не має доступу.

    Returns:
        User: Поточний користувач із правами модератора чи адміністратора.
    """
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail=messages.role_access)
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Перевіряє, що користувач має роль ADMIN.

    Args:
        current_user (User): Поточний користувач (DI через Depends).

    Raises:
        HTTPException(403): Якщо користувач не адміністратор.

    Returns:
        User: Поточний користувач-адміністратор.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=messages.role_access)
    return current_user
