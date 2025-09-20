from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.repositories.contacts_repository import ContactRepository
from src.schemas.contacts_schema import ContactSchema, ContactUpdateSchema


class ContactService:
    def __init__(self, db: AsyncSession):
        self.contact_repository = ContactRepository(db)

    async def create_contact(self, body: ContactSchema, user: User) -> Contact:
        return await self.contact_repository.create_contact(body, user)

    async def get_all_contacts(
        self, user: User, limit: int, offset: int
    ) -> Sequence[Contact]:
        return await self.contact_repository.get_all_contacts(user, limit, offset)

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        return await self.contact_repository.get_contact_by_id(contact_id, user)

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        return await self.contact_repository.remove_contact(contact_id, user)

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user: User
    ) -> Contact | None:
        return await self.contact_repository.update_contact(contact_id, body, user)

    async def get_contact_by_query(self, query: str, user: User) -> Sequence[Contact]:
        return await self.contact_repository.get_contact_by_query(query, user)

    async def get_contacts_by_upcoming_birthdays(
        self, user: User, days: int = 7
    ) -> Sequence[Contact]:
        return await self.contact_repository.get_contacts_by_upcoming_birthdays(
            user, days=days
        )

    async def get_by_email_or_phone(
        self, email: str, phone: str, user: User
    ) -> Contact | None:
        return await self.contact_repository.get_by_email_or_phone(email, phone, user)

    async def exists_other_with_email_or_phone(
        self, contact_id: int, email: str | None, phone: str | None, user: User
    ) -> bool:
        return await self.contact_repository.exists_other_with_email_or_phone(
            user, contact_id, email, phone
        )
