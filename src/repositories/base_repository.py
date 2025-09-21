from typing import TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    """
    Базовий репозиторій для роботи з моделями SQLAlchemy.

    Інкапсулює CRUD-операції для узагальнених моделей.
    Використовується як батьківський клас для конкретних репозиторіїв.

    Args:
        session (AsyncSession): Асинхронна сесія SQLAlchemy.
        model (Type[ModelType]): Модель, з якою працює репозиторій.
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        """
        Ініціалізує базовий репозиторій.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy для взаємодії з БД.
            model (Type[ModelType]): Модель (ORM-клас), для якої виконується CRUD.
        """
        self.db = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        """
        Отримати всі записи моделі.

        Returns:
            list[ModelType]: Список усіх записів у таблиці.
        """
        stmt = select(self.model)
        contacts = await self.db.execute(stmt)
        return list(contacts.scalars().all())

    async def get_by_id(self, _id: int) -> ModelType | None:
        """
        Отримати запис за його ідентифікатором.

        Args:
            _id (int): Ідентифікатор запису.

        Returns:
            ModelType | None: Знайдений запис або None, якщо не існує.
        """
        result = await self.db.execute(select(self.model).where(self.model.id == _id))
        return result.scalars().first()

    async def create(self, instance: ModelType) -> ModelType:
        """
        Створити новий запис.

        Args:
            instance (ModelType): Екземпляр моделі для збереження.

        Returns:
            ModelType: Створений екземпляр моделі з оновленим id.
        """
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """
        Оновити існуючий запис.

        Args:
            instance (ModelType): Екземпляр моделі з оновленими даними.

        Returns:
            ModelType: Оновлений екземпляр моделі.
        """
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """
        Видалити запис із бази.

        Args:
            instance (ModelType): Екземпляр моделі для видалення.

        Returns:
            None
        """
        await self.db.delete(instance)
        await self.db.commit()
