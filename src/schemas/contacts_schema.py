from datetime import date, datetime
from typing import Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)

from src.conf import messages
from src.conf import constants


class ContactSchema(BaseModel):
    """Схема створення контакту."""

    first_name: str = Field(
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_fname,
    )
    last_name: str = Field(
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_lname,
    )
    email: EmailStr = Field(
        min_length=constants.EMAIL_MIN_LENGTH,
        max_length=constants.EMAIL_MAX_LENGTH,
        description=messages.contact_schema_email,
    )
    phone: str = Field(
        min_length=constants.PHONE_MIN_LENGTH,
        max_length=constants.PHONE_MAX_LENGTH,
        description=messages.contact_schema_phone,
    )
    birthday: date = Field(description=messages.contact_schema_birthday)
    additional_info: Optional[str] = Field(
        default=None, max_length=255, description=messages.contact_schema_add_info
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "first_name": "Оксана",
                "last_name": "Дончук",
                "email": "oksana@example.com",
                "phone": "+380501112233",
                "birthday": "1980-02-09",
                "additional_info": "Студентка університету",
            }
        },
    )

    # нормалізація рядків
    @field_validator("first_name", "last_name", "phone", mode="before")
    def _strip(cls, val: str) -> str:
        return val.strip() if isinstance(val, str) else val

    @field_validator("email", mode="before")
    def _email_lower(cls, val: str) -> str:
        return val.strip().lower() if isinstance(val, str) else val

    # бізнес-умова: день народження не може бути в майбутньому
    @field_validator("birthday")
    def _birthday_not_in_future(cls, val: date) -> date:
        if val > date.today():
            raise ValueError(f"{messages.validate_birthday}")
        return val


class ContactUpdateSchema(BaseModel):
    """Схема оновлення контакту (усі поля опційні)."""

    first_name: Optional[str] = Field(
        default=None,
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_fname,
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=constants.NAME_MIN_LENGTH,
        max_length=constants.NAME_MAX_LENGTH,
        description=messages.contact_schema_lname,
    )
    email: Optional[EmailStr] = Field(
        default=None,
        min_length=constants.EMAIL_MIN_LENGTH,
        max_length=constants.EMAIL_MAX_LENGTH,
        description=messages.contact_schema_email,
    )
    phone: Optional[str] = Field(
        default=None,
        min_length=constants.PHONE_MIN_LENGTH,
        max_length=constants.PHONE_MAX_LENGTH,
        description=messages.contact_schema_phone,
    )
    birthday: Optional[date] = Field(
        default=None, description=messages.contact_schema_birthday
    )
    additional_info: Optional[str] = Field(
        default=None, max_length=255, description=messages.contact_schema_add_info
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("first_name", "last_name", "phone", mode="before")
    def _strip(cls, val: Optional[str]) -> Optional[str]:
        return val.strip() if isinstance(val, str) else val

    @field_validator("email", mode="before")
    def _email_lower(cls, val: Optional[str]) -> Optional[str]:
        return val.strip().lower() if isinstance(val, str) else val

    @field_validator("birthday")
    def _birthday_not_in_future(cls, val: Optional[date]) -> Optional[date]:
        if val and val > date.today():
            raise ValueError(f"{messages.validate_birthday}")
        return val

    @model_validator(mode="after")
    def _at_least_one_field(self):
        # перевіряємо, що передано хоча б одне поле для оновлення
        if not any(
            [
                self.first_name,
                self.last_name,
                self.email,
                self.phone,
                self.birthday,
                self.additional_info,
            ]
        ):
            raise ValueError("Потрібно передати хоча б одне поле для оновлення")
        return self


class ContactResponse(BaseModel):
    """Схема відповіді з повною інформацією про контакт."""

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birthday: date
    additional_info: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")
