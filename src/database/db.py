import contextlib
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


class DatabaseSessionManager:
    """
    Менеджер для роботи з асинхронними сесіями SQLAlchemy.

    Створює engine та фабрику асинхронних сесій, що дозволяє
    працювати з базою даних у контексті FastAPI.

    Args:
        url (str): Рядок підключення до бази даних у форматі:
            ``postgresql+asyncpg://user:password@host:port/dbname``.
    """

    def __init__(self, url: str):
        self._engine: AsyncEngine = create_async_engine(url, echo=False)
        self._session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            bind=self._engine,
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Асинхронний контекст-менеджер для роботи з базою даних.

        Забезпечує автоматичний rollback у випадку помилок
        та закриває сесію після завершення роботи.

        Yields:
            AsyncSession: Асинхронна сесія SQLAlchemy для виконання запитів.

        Raises:
            SQLAlchemyError: Помилка при роботі з базою даних.
            Exception: Інші непередбачені помилки.
        """
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


# Глобальний екземпляр менеджера
sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Залежність для FastAPI (Depends).

    Використовується для отримання асинхронної сесії БД у роутерах та сервісах.

    Yields:
        AsyncSession: Асинхронна сесія SQLAlchemy для виконання запитів.
    """
    async with sessionmanager.session() as session:
        yield session
