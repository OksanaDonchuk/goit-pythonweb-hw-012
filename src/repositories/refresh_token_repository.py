from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken
from src.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository):
    """
    Репозиторій для роботи з refresh-токенами.

    Успадковує базові CRUD-операції з :class:`BaseRepository`
    та додає методи для пошуку, збереження й відкликання refresh-токенів.
    """

    def __init__(self, session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі :class:`RefreshToken`.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(session, RefreshToken)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """
        Повертає refresh-токен за його хешем.

        Args:
            token_hash (str): Хеш токена.

        Returns:
            RefreshToken | None: Токен або None, якщо не знайдено.
        """
        stmt = select(self.model).where(RefreshToken.token_hash == token_hash)
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def get_active_token(
        self, token_hash: str, current_time: datetime
    ) -> RefreshToken | None:
        """
        Отримати активний (непрострочений і не відкликаний) refresh-токен.

        Args:
            token_hash (str): Хеш токена.
            current_time (datetime): Поточний час для перевірки дати закінчення.

        Returns:
            RefreshToken | None: Активний токен або None, якщо не знайдено.
        """
        stmt = select(self.model).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expired_at > current_time,
            RefreshToken.revoked_at.is_(None),
        )
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def save_token(
        self,
        user_id: int,
        token_hash: str,
        expired_at: datetime,
        ip_address: str,
        user_agent: str,
    ) -> RefreshToken:
        """
        Зберегти новий refresh-токен у базі.

        Args:
            user_id (int): ID користувача.
            token_hash (str): Унікальний хеш токена.
            expired_at (datetime): Дата закінчення дії токена.
            ip_address (str): IP-адреса, з якої виконано вхід.
            user_agent (str): User-Agent клієнта.

        Returns:
            RefreshToken: Створений токен.
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expired_at=expired_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(refresh_token)

    async def revoke_token(self, refresh_token: RefreshToken) -> None:
        """
        Відкликати refresh-токен (зробити його недійсним).

        Args:
            refresh_token (RefreshToken): Токен, який потрібно відкликати.

        Returns:
            None
        """
        refresh_token.revoked_at = datetime.now()
        await self.db.commit()
