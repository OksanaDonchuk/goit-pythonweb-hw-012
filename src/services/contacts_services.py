from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.repositories.contacts_repository import ContactRepository
from src.schemas.contacts_schema import ContactSchema, ContactUpdateSchema


class ContactService:
    """
    Сервіс для роботи з контактами.

    Інкапсулює бізнес-логіку поверх репозиторію `ContactRepository`.
    Використовується в роутерах для виконання CRUD-операцій над контактами.
    """

    def __init__(self, db: AsyncSession):
        """
        Ініціалізує сервіс контактів.

        Args:
            db (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        self.contact_repository = ContactRepository(db)

    async def create_contact(self, body: ContactSchema, user: User) -> Contact:
        """
        Створює новий контакт для користувача.

        Args:
            body (ContactSchema): Дані контакту (ім’я, email, телефон тощо).
            user (User): Авторизований користувач.

        Returns:
            Contact: Створений контакт.
        """
        return await self.contact_repository.create_contact(body, user)

    async def get_all_contacts(
        self, user: User, limit: int, offset: int
    ) -> Sequence[Contact]:
        """
        Повертає всі контакти користувача з пагінацією.

        Args:
            user (User): Авторизований користувач.
            limit (int): Кількість контактів для вибірки.
            offset (int): Зсув від початку списку.

        Returns:
            Sequence[Contact]: Список контактів.
        """
        return await self.contact_repository.get_all_contacts(user, limit, offset)

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Отримує контакт за його ID.

        Args:
            contact_id (int): Ідентифікатор контакту.
            user (User): Авторизований користувач.

        Returns:
            Contact | None: Контакт, якщо знайдений, або None.
        """
        return await self.contact_repository.get_contact_by_id(contact_id, user)

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Видаляє контакт користувача за його ID.

        Args:
            contact_id (int): Ідентифікатор контакту.
            user (User): Авторизований користувач.

        Returns:
            Contact | None: Видалений контакт або None, якщо не знайдено.
        """
        return await self.contact_repository.remove_contact(contact_id, user)

    async def update_contact(
        self, contact_id: int, body: ContactUpdateSchema, user: User
    ) -> Contact | None:
        """
        Оновлює дані контакту користувача.

        Args:
            contact_id (int): Ідентифікатор контакту.
            body (ContactUpdateSchema): Нові дані контакту.
            user (User): Авторизований користувач.

        Returns:
            Contact | None: Оновлений контакт або None, якщо не знайдено.
        """
        return await self.contact_repository.update_contact(contact_id, body, user)

    async def get_contact_by_query(self, query: str, user: User) -> Sequence[Contact]:
        """
        Шукає контакти за ім’ям, прізвищем або email.

        Args:
            query (str): Рядок пошуку.
            user (User): Авторизований користувач.

        Returns:
            Sequence[Contact]: Список контактів, що відповідають пошуку.
        """
        return await self.contact_repository.get_contact_by_query(query, user)

    async def get_contacts_by_upcoming_birthdays(
        self, user: User, days: int = 7
    ) -> Sequence[Contact]:
        """
        Повертає контакти користувача, у яких день народження в найближчі `days` днів.

        Args:
            user (User): Авторизований користувач.
            days (int, optional): Кількість днів наперед. За замовчуванням 7.

        Returns:
            Sequence[Contact]: Список відповідних контактів.
        """
        return await self.contact_repository.get_contacts_by_upcoming_birthdays(
            user, days=days
        )

    async def get_by_email_or_phone(
        self, email: str, phone: str, user: User
    ) -> Contact | None:
        """
        Шукає контакт за email або телефоном.

        Args:
            email (str): Електронна пошта.
            phone (str): Телефонний номер.
            user (User): Авторизований користувач.

        Returns:
            Contact | None: Контакт, якщо знайдено, або None.
        """
        return await self.contact_repository.get_by_email_or_phone(email, phone, user)

    async def exists_other_with_email_or_phone(
        self, contact_id: int, email: str | None, phone: str | None, user: User
    ) -> bool:
        """
        Перевіряє, чи існує інший контакт користувача з тим самим email або телефоном.

        Args:
            contact_id (int): ID контакту, що оновлюється (його виключаємо).
            email (str | None): Новий email (може бути None).
            phone (str | None): Новий телефон (може бути None).
            user (User): Авторизований користувач.

        Returns:
            bool: True, якщо конфлікт існує, False — якщо ні.
        """
        return await self.contact_repository.exists_other_with_email_or_phone(
            user, contact_id, email, phone
        )
