from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.conf import messages
from src.database.db import get_db

router = APIRouter(tags=["utils"])


@router.get(
    "/healthchecker",
    name="Перевірка стану застосунку",
    description="Ендпоінт для перевірки працездатності застосунку та підключення до бази даних. "
    "Виконує простий SQL-запит (`SELECT 1`) і повертає повідомлення про успіх у разі, "
    "якщо база даних доступна.",
    response_description="JSON-повідомлення про стан застосунку.",
)
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Перевіряє, чи доступна база даних та чи працює застосунок.

    Args:
        db (AsyncSession): Сесія підключення до бази даних.

    Returns:
        dict: Повідомлення про працездатність застосунку.

    Raises:
        HTTPException: 500, якщо підключення до бази даних неможливе.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=messages.db_conf_not_success,
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=messages.db_conn_error,
        )
