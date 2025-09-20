from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken
from src.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session, RefreshToken)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:

        stmt = select(self.model).where(RefreshToken.token_hash == token_hash)
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def get_active_token(
        self, token_hash: str, current_time: datetime
    ) -> RefreshToken | None:
        """Get active refresh token by token hash."""
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

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expired_at=expired_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(refresh_token)

    async def revoke_token(self, refresh_token: RefreshToken) -> None:

        refresh_token.revoked_at = datetime.now()
        await self.db.commit()
