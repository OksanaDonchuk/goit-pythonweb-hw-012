from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.core.email_token import get_email_from_token, create_email_token
from src.entity.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.user_schema import UserCreate
from src.services.auth_services import AuthService
from src.services.email_services import send_email


class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:

        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:

        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:

        user = await self.user_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        user = await self.user_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        return await self.user_repository.update_avatar_url(email, url)

    async def reset_password(self, token: str, new_password: str) -> dict:
        """
        Скидає пароль користувача за валідним токеном.

        1) Розкодовує токен та дістає email.
        2) Перевіряє існування користувача.
        3) Хешує новий пароль та оновлює у БД через репозиторій.

        Raises:
            HTTPException(404): Якщо користувача не знайдено.
            HTTPException(422): Якщо токен невалідний (піднімається у get_email_from_token).

        Returns:
            dict: Повідомлення про успіх.
        """
        email = get_email_from_token(token)
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=messages.user_not_found,
            )

        hashed = self.auth_service._hash_password(new_password)
        await self.user_repository.update_password(email, hashed)

        return {"message": messages.password_reset_success}
