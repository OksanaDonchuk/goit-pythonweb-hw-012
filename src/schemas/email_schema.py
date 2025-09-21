from pydantic import BaseModel, EmailStr


class RequestEmail(BaseModel):
    """
    Схема запиту на повторне підтвердження електронної пошти.

    Використовується, коли користувач надсилає свою email-адресу
    для отримання нового листа з токеном підтвердження.

    Attributes:
        email (EmailStr): Валідована адреса електронної пошти користувача.
    """

    email: EmailStr
