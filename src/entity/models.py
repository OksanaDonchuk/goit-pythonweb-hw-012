from datetime import datetime, date
from enum import Enum

from sqlalchemy import (
    String,
    DateTime,
    func,
    Date,
    ForeignKey,
    UniqueConstraint,
    Text,
    Enum as SqlEnum,
    Boolean,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.conf import constants


class Base(DeclarativeBase):
    """Базовий клас для всіх моделей SQLAlchemy."""

    pass


class Contact(Base):
    """
    Модель контакту.

    Таблиця зберігає інформацію про контакт, прив’язаний до користувача:
    - ім'я, прізвище;
    - унікальні email і телефон у межах одного користувача;
    - дату народження та додаткові дані;
    - дату створення та оновлення запису;
    - зв’язок з користувачем (user_id).
    """

    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("email", "user_id", name="unique_contact_user_email"),
        UniqueConstraint("phone", "user_id", name="unique_contact_user_phone"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(
        String(constants.NAME_MAX_LENGTH), nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(constants.NAME_MAX_LENGTH), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(constants.EMAIL_MAX_LENGTH), nullable=False
    )
    phone: Mapped[str] = mapped_column(
        String(constants.PHONE_MAX_LENGTH), nullable=False
    )
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    additional_info: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    user: Mapped["User"] = relationship("User", backref="contacts", lazy="joined")

    def __repr__(self) -> str:
        """Повертає рядкове представлення контакту для відлагодження."""
        return (
            f"Contact(id={self.id}, first_name='{self.first_name}', "
            f"last_name='{self.last_name}', email='{self.email}', "
            f"phone='{self.phone}', birthday={self.birthday})"
        )


class UserRole(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class User(Base):
    """
    Модель користувача.

    Використовується для авторизації та прив’язки контактів:
    - зберігає унікальний username та email;
    - зберігає хешований пароль;
    - має зв’язок із refresh-токенами.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str] = mapped_column(
        String(constants.EMAIL_MAX_LENGTH), nullable=False, unique=True
    )
    hash_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole), default=UserRole.USER, nullable=False
    )
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )


class RefreshToken(Base):
    """
    Модель refresh-токена.

    Використовується для реалізації механізму оновлення доступу:
    - зберігає унікальний хеш токена;
    - дату створення, закінчення та відкликання;
    - інформацію про IP та User-Agent для безпеки;
    - належить конкретному користувачу.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(nullable=False, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    expired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
