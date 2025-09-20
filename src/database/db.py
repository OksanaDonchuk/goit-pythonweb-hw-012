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
    Менеджер для створення асинхронного engine та фабрики сесій SQLAlchemy.

    Args:
        url (str): Рядок підключення до бази даних у форматі
            postgresql+asyncpg://user:password@host:port/dbname
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

        Yields:
            AsyncSession: Асинхронна сесія SQLAlchemy для виконання запитів.

        Raises:
            SQLAlchemyError: Якщо виникає помилка бази даних.
            Exception: Для будь-яких інших неочікуваних помилок.
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
    Генератор залежності для FastAPI.

    Використовується у Depends(), щоб передавати асинхронну сесію у роутери.

    Yields:
        AsyncSession: Асинхронна сесія SQLAlchemy.
    """
    async with sessionmanager.session() as session:
        yield session
