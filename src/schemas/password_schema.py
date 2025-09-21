from pydantic import BaseModel, EmailStr, Field

from src.conf import constants


class ResetPasswordRequestSchema(BaseModel):
    """
    Схема запиту на скидання пароля.

    Використовується, коли користувач надсилає свою email-адресу,
    щоб отримати лист із токеном для скидання пароля.

    Attributes:
        email (EmailStr): Валідована адреса електронної пошти користувача.
    """

    email: EmailStr


class ResetPasswordSchema(BaseModel):
    """
    Схема скидання пароля.

    Використовується для надсилання токена та нового паролю
    після підтвердження запиту на скидання.

    Attributes:
        token (str): JWT-токен, отриманий у листі для скидання пароля.
        new_password (str): Новий пароль користувача. Валідований за мінімальною
            та максимальною довжиною.
    """

    token: str
    new_password: str = Field(
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )
