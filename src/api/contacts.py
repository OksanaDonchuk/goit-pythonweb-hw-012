from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.core.depend_service import get_current_user
from src.database.db import get_db
from src.entity.models import User
from src.services.contacts_services import ContactService
from src.schemas.contacts_schema import (
    ContactSchema,
    ContactUpdateSchema,
    ContactResponse,
)
from src.conf import messages

router = APIRouter(prefix="/contacts", tags=["contacts"])


def get_contact_service(db: AsyncSession = Depends(get_db)) -> ContactService:
    """
    Повертає сервіс для роботи з контактами.

    Args:
        db: Асинхронна сесія SQLAlchemy (DI через Depends).

    Returns:
        ContactService: Сервіс із бізнес-логікою над контактами.
    """
    return ContactService(db)


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    name="Створення контакту",
    description="Створює контакт. Якщо email або телефон вже існують — повертає 409.",
    response_description="Повертає дані створеного контакту для авторизованого користувача.",
)
async def create_contact(
    body: ContactSchema,
    service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user),
):
    """
    Створює новий контакт з перевіркою унікальності для авторизованого користувача

    - Спочатку перевіряємо, чи існує контакт з таким email або телефоном.
    - Якщо так — 409 CONFLICT.
    - Якщо ні — створюємо запис.

    Плюс додаткова «страховка» від конкуренції: ловимо IntegrityError,
    якщо унікальні індекси БД спрацювали раніше (race condition).
    """
    existing = await service.get_by_email_or_phone(str(body.email), body.phone, user)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Контакт з email '{body.email}' або телефоном '{body.phone}' вже існує",
        )

    return await service.create_contact(body, user)


@router.get(
    "/",
    response_model=list[ContactResponse],
    name="Всі контакти",
    description="Вибирає з бази даних всі контакти з пагінацією",
    response_description="Повертає список всіх контактів користувача",
)
async def get_all_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user),
):
    """
    Отримує список контактів користувача з пагінацією.

    Args:
        limit: Максимальна кількість записів.
        offset: Зсув від початку вибірки.
        service: Сервіс контактів (DI).
        user: Авторизований користувач - власник контактів.

    Returns:
        list[ContactResponse]: Список контактів (може бути порожнім).
    """
    return await service.get_all_contacts(user, limit, offset)


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    name="Пошук за id",
    description="Шукає контакт за його id",
    response_description="Повертає контакт за його id або 404, якщо не знайдено",
)
async def get_contact_by_id(
    contact_id: int,
    service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user),
):
    """
    Отримує контакт за ідентифікатором, якщо він є в контактах користувача.

    Args:
        contact_id: Ідентифікатор контакту.
        service: Сервіс контактів (DI).
        user: Авторизований користувач - власник контактів.

    Raises:
        HTTPException(404): Якщо контакт не знайдено.

    Returns:
        ContactResponse: Знайдений контакт.
    """
    contact = await service.get_contact_by_id(contact_id, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=messages.contact_not_found,
        )
    return contact


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
    name="Оновлення контакту користувача",
    description="Оновлює дані контакту. Перевіряє унікальність email та телефону.",
    response_description="Повертає оновлений контакт користувача або 404, якщо не знайдено.",
)
async def update_contact(
    contact_id: int,
    body: ContactUpdateSchema,
    service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user),
):
    """
    Оновлює контакт користувача із перевіркою унікальності email та телефону.

    Args:
        contact_id: Ідентифікатор контакту.
        body: Дані для оновлення (будь-яке поле може бути None).
        service: Сервіс контактів.
        user: Авторизований користувач - власник контактів.

    Raises:
        HTTPException(404): Якщо контакт не знайдено.
        HTTPException(409): Якщо email або телефон вже використовуються іншим контактом.

    Returns:
        ContactResponse: Оновлений контакт.
    """
    update_data = body.model_dump(exclude_unset=True)

    # Перевірка унікальності тільки якщо передано email/phone
    email = update_data.get("email")
    phone = update_data.get("phone")

    if email or phone:
        exists_conflict = await service.exists_other_with_email_or_phone(
            contact_id, email, phone, user
        )
        if exists_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Інший контакт вже має цей email або телефон",
            )

    contact = await service.update_contact(contact_id, body, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=messages.contact_not_found,
        )
    return contact


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    name="Видалення контакта користувача",
    description="Видаляє контакт за його id",
    response_description="Повертає None або 404, якщо контакту немає",
)
async def delete_contact(
    contact_id: int,
    service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user),
):
    """
    Видаляє контакт користувача за ідентифікатором.

    Args:
        contact_id: Ідентифікатор контакту.
        service: Сервіс контактів (DI).
        user: Авторизований користувач - власник контактів

    Raises:
        HTTPException(404): Якщо контакт не знайдено.

    Returns:
        None
    """
    contact = await service.remove_contact(contact_id, user)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=messages.contact_not_found,
        )
    return None


@router.get(
    "/search/",
    response_model=list[ContactResponse],
    name="Пошук контакту користувача по параметрам",
    description="Пошук контакту за ім'ям, прізвищем або поштою",
    response_description="Повертає список контактів (може бути порожнім)",
)
async def get_contact_by_query(
    query: str = Query(..., min_length=1, max_length=100, example="Оксана"),
    service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user),
):
    """
    Повертає список контактів користувача, що відповідають рядку пошуку (ILike).

    Args:
        query: Рядок пошуку (по first_name, last_name, email).
        service: Сервіс контактів (DI).
        user: Авторизований користувач - власник контактів

    Returns:
        list[ContactResponse]: Список відповідних контактів (може бути порожнім).
    """
    return await service.get_contact_by_query(query, user)


@router.get(
    "/upcoming_birthdays/",
    response_model=list[ContactResponse],
    name="Контакти користувача за ДН",
    description="Список контактів, у яких день народження у найближчі дні від 1 до 30 (обирається користувачем)",
    response_description="Повертає список контактів або повідомлення, якщо список порожній",
)
async def get_contacts_by_upcoming_birthdays(
    days: int = Query(7, ge=1, le=30),
    service: ContactService = Depends(get_contact_service),
    user: User = Depends(get_current_user),
):
    """
    Повертає контакти користувача з днями народження в найближчі `days` днів.

    Якщо нічого не знайдено — повертає 200 OK з JSON-об’єктом:
    `{"message": "...", "contacts": []}`.

    Args:
        days: Кількість днів наперед (1–30).
        service: Сервіс контактів (DI).
        user: Авторизований користувач - власник контактів

    Returns:
        list[ContactResponse] | JSONResponse: Список контактів або повідомлення з порожнім списком.
    """
    contacts = await service.get_contacts_by_upcoming_birthdays(user, days=days)
    if not contacts:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Немає контактів з ДН у найближчі {days} днів",
                "contacts": [],
            },
        )
    return contacts
