from pydantic import BaseModel


class TokenResponse(BaseModel):
    """
    Схема відповіді з токенами автентифікації.

    Використовується для повернення пари access- і refresh-токенів
    після успішної авторизації чи оновлення токенів.

    Attributes:
        access_token (str): JWT-токен доступу, що використовується для авторизації запитів.
        token_type (str): Тип токена. За замовчуванням "bearer".
        refresh_token (str): JWT-токен оновлення для отримання нової пари токенів.
    """

    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """
    Схема запиту для оновлення токенів.

    Використовується клієнтом для відправки refresh-токена,
    щоб отримати новий access- і refresh-токен.

    Attributes:
        refresh_token (str): Дійсний refresh-токен користувача.
    """

    refresh_token: str
