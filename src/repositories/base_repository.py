from typing import TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.db = session
        self.model = model

    async def get_all(self) -> list[ModelType]:

        stmt = select(self.model)
        contacts = await self.db.execute(stmt)
        return list(contacts.scalars().all())

    async def get_by_id(self, _id: int) -> ModelType | None:

        result = await self.db.execute(select(self.model).where(self.model.id == _id))
        return result.scalars().first()

    async def create(self, instance: ModelType) -> ModelType:

        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:

        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:

        await self.db.delete(instance)
        await self.db.commit()
