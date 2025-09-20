from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator

from src.conf import constants
from src.conf import messages
from src.entity.models import UserRole


class UserBase(BaseModel):

    username: str = Field(
        min_length=constants.USERNAME_MIN_LENGTH,
        max_length=constants.USERNAME_MAX_LENGTH,
        description=messages.user_schema_name,
    )
    email: EmailStr

    @field_validator("username", mode="before")
    def _strip(cls, val: str) -> str:
        return val.strip() if isinstance(val, str) else val

    @field_validator("email", mode="before")
    def _email_lower(cls, val: str) -> str:
        return val.strip().lower() if isinstance(val, str) else val


class UserCreate(UserBase):

    password: str = Field(
        min_length=constants.USER_PASSWORD_MIN_LENGTH,
        max_length=constants.USER_PASSWORD_MAX_LENGTH,
        description=messages.user_schema_password,
    )


class UserResponse(UserBase):

    id: int
    avatar: str | None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
