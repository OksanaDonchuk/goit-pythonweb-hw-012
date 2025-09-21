"""
Модуль конфігурації застосунку.

Містить клас Settings для зчитування змінних оточення з `.env` файлу
за допомогою Pydantic. Використовується для налаштування бази даних,
JWT-токенів, Redis, поштового сервісу та Cloudinary.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict, EmailStr


class Settings(BaseSettings):
    """
    Клас конфігурації застосунку.

    Значення беруться з `.env` файлу або змінних середовища.
    Використовується для збереження конфігураційних параметрів
    бази даних, поштового сервісу, Redis, JWT та Cloudinary.

    Attributes:
        DB_URL (str): URL підключення до бази даних PostgreSQL.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): Час життя access-токена в хвилинах.
        REFRESH_TOKEN_EXPIRE_DAYS (int): Час життя refresh-токена в днях.
        ALGORITHM (str): Алгоритм шифрування для JWT.
        SECRET_KEY (str): Секретний ключ для підпису JWT.
        REDIS_URL (str): Адреса підключення до Redis.
        MAIL_USERNAME (EmailStr): Логін поштового акаунту.
        MAIL_PASSWORD (str): Пароль поштового акаунту.
        MAIL_FROM (EmailStr): Email, з якого відправляються повідомлення.
        MAIL_PORT (int): Порт поштового сервера.
        MAIL_SERVER (str): Адреса поштового сервера.
        MAIL_FROM_NAME (str): Ім'я відправника в листах.
        MAIL_STARTTLS (bool): Використовувати STARTTLS.
        MAIL_SSL_TLS (bool): Використовувати SSL/TLS.
        USE_CREDENTIALS (bool): Використовувати авторизацію для SMTP.
        VALIDATE_CERTS (bool): Перевіряти SSL-сертифікати.
        CLD_NAME (str): Назва акаунта Cloudinary.
        CLD_API_KEY (int): API-ключ Cloudinary.
        CLD_API_SECRET (str): Секрет Cloudinary.
    """

    DB_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/db"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    SECRET_KEY: str = "secret"

    REDIS_URL: str = "redis://localhost"

    MAIL_USERNAME: EmailStr = "fake@example.com"
    MAIL_PASSWORD: str = "password"
    MAIL_FROM: EmailStr = "fake@example.com"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.example.com"
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    CLD_NAME: str = "cloud"
    CLD_API_KEY: int = 12345
    CLD_API_SECRET: str = "secret"

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
