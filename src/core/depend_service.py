from fastapi import Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.services.auth_services import AuthService, oauth2_scheme
from src.services.user_services import UserService
from src.entity.models import User, UserRole
from src.database.db import get_db


def get_auth_service(db: AsyncSession = Depends(get_db)):

    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)):

    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):

    return await auth_service.get_current_user(token)


def get_current_moderator_user(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail=messages.role_access)
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=messages.role_access)
    return current_user
