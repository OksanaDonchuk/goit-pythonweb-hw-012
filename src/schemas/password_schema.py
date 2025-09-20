from pydantic import BaseModel, EmailStr, Field

from src.conf import constants


class ResetPasswordRequestSchema(BaseModel):

    email: EmailStr


class ResetPasswordSchema(BaseModel):

    token: str
    new_password: str = Field(
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
    )
