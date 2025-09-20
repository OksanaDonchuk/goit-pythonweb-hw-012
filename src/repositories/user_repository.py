from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.base_repository import BaseRepository
from src.schemas.user_schema import UserCreate


class UserRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:

        stmt = select(self.model).where(User.username == username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:

        stmt = select(self.model).where(User.email == email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self, user_data: UserCreate, hashed_password: str, avatar: str
    ) -> User:

        user = User(
            **user_data.model_dump(exclude_unset=True, exclude={"password"}),
            hash_password=hashed_password,
        )
        return await self.create(user)

    async def confirmed_email(self, email: str) -> None:
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, email: str, hashed_password: str) -> User:
        user = await self.get_user_by_email(email)
        user.hash_password = hashed_password
        await self.db.commit()
        await self.db.refresh(user)
        return user
