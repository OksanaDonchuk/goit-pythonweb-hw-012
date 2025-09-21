from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.core.email_token import get_email_from_token
from src.entity.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.user_schema import UserCreate
from src.services.auth_services import AuthService


class UserService:
    """
    Сервіс для роботи з користувачами.

    Інкапсулює бізнес-логіку над користувачами та делегує роботу
    до відповідних репозиторіїв (`UserRepository`) та `AuthService`.
    """

    def __init__(self, db: AsyncSession):
        """
        Ініціалізує сервіс користувачів.

        Args:
            db (AsyncSession): Асинхронна сесія SQLAlchemy для роботи з БД.
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Створює нового користувача через `AuthService`.

        Args:
            user_data (UserCreate): Дані користувача (username, email, пароль).

        Returns:
            User: Створений користувач.
        """
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Отримує користувача за username.

        Args:
            username (str): Ім’я користувача.

        Returns:
            User | None: Користувач або None, якщо не знайдено.
        """
        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Отримує користувача за email.

        Args:
            email (str): Електронна пошта користувача.

        Returns:
            User | None: Користувач або None, якщо не знайдено.
        """
        user = await self.user_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Позначає email користувача як підтверджений.

        Args:
            email (str): Електронна пошта користувача.
        """
        user = await self.user_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        """
        Оновлює URL аватара користувача.

        Args:
            email (str): Електронна пошта користувача.
            url (str): Новий URL аватара.

        Returns:
            User: Користувач з оновленим аватаром.
        """
        return await self.user_repository.update_avatar_url(email, url)

    async def reset_password(self, token: str, new_password: str) -> dict:
        """
        Скидає пароль користувача за валідним токеном.

        1. Розкодовує токен та отримує email.
        2. Перевіряє існування користувача.
        3. Хешує новий пароль та оновлює його у БД.

        Args:
            token (str): JWT токен, виданий для скидання пароля.
            new_password (str): Новий пароль користувача.

        Raises:
            HTTPException(404): Якщо користувача не знайдено.
            HTTPException(422): Якщо токен недійсний.

        Returns:
            dict: Повідомлення про успішне скидання пароля.
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
