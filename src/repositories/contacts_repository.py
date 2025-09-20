from typing import Sequence

from sqlalchemy import select, or_, func, case, literal, cast, Integer, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contacts_schema import ContactSchema, ContactUpdateSchema


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_contact(self, body: ContactSchema, user: User) -> Contact:
        contact = Contact(**body.model_dump(), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def get_all_contacts(
        self, user: User, limit: int = 100, offset: int = 0
    ) -> Sequence[Contact]:
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .order_by(Contact.id)
            .offset(offset)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        stmt = select(Contact).filter_by(id=contact_id, user_id=user.id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user: User
    ) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if not contact:
            return None

        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)

        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if not contact:
            return None

        await self.db.delete(contact)
        await self.db.commit()
        return contact

    async def get_contact_by_query(
        self, query: str, user: User, *, limit: int = 100, offset: int = 0
    ) -> Sequence[Contact]:
        if not query:
            return []
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .where(
                or_(
                    Contact.first_name.ilike(f"%{query}%"),
                    Contact.last_name.ilike(f"%{query}%"),
                    Contact.email.ilike(f"%{query}%"),
                )
            )
            .order_by(Contact.id)
            .offset(offset)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_contacts_by_upcoming_birthdays(
        self, user: User, days: int = 7
    ) -> Sequence[Contact]:
        """
        Контакти, в яких день народження у найближчі `days` днів (включно з сьогодні).
        Враховує різні роки
        """
        year = cast(func.extract("year", func.current_date()), Integer)
        month = cast(func.extract("month", Contact.birthday), Integer)
        day = cast(func.extract("day", Contact.birthday), Integer)

        # ДН у поточному році
        this_year_bday = func.make_date(year, month, day)

        # Якщо вже минуло — переносимо на наступний рік
        next_birthday = case(
            (
                this_year_bday < func.current_date(),
                this_year_bday + text("interval '1 year'"),
            ),
            else_=this_year_bday,
        )

        # Верхня межа діапазону
        upper = func.current_date() + text(f"interval '{days} days'")

        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .where(next_birthday.between(func.current_date(), upper))
            .order_by(
                next_birthday.asc(), Contact.last_name.asc(), Contact.first_name.asc()
            )
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_by_email_or_phone(
        self, email: str, phone: str, user: User
    ) -> Contact | None:
        """
        Повертає контакт, якщо існує збіг за email або телефоном.

        Args:
            email: Електронна пошта для точного порівняння (нормалізована у схемі).
            phone: Телефон для точного порівняння (нормалізований у схемі).

        Returns:
            Contact | None: Перший знайдений контакт або None.
        """
        stmt = (
            select(Contact)
            .filter_by(user_id=user.id)
            .where(or_(Contact.email == email, Contact.phone == phone))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def exists_other_with_email_or_phone(
        self,
        user: User,
        contact_id: int,
        email: str | None = None,
        phone: str | None = None,
    ) -> bool:
        """
        Перевіряє, чи існує інший контакт з таким email або телефоном.

        Args:
            contact_id: ID контакту, якого оновлюємо (виключається з перевірки).
            email: Новий email (може бути None, якщо не оновлюється).
            phone: Новий телефон (може бути None, якщо не оновлюється).

        Returns:
            bool: True, якщо знайдено інший контакт з таким email або телефоном.
        """
        stmt = (
            select(Contact).filter_by(user_id=user.id).where(Contact.id != contact_id)
        )

        if email:
            stmt = stmt.where(Contact.email == email)
        if phone:
            stmt = stmt.where(Contact.phone == phone)

        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None
