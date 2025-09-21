from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Request,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth_services import AuthService, oauth2_scheme
from src.schemas.token_schema import TokenResponse, RefreshTokenRequest
from src.schemas.user_schema import UserResponse, UserCreate
from src.services.email_services import send_email

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """
    Залежність для отримання екземпляра AuthService.

    Args:
        db (AsyncSession): Асинхронна сесія SQLAlchemy.

    Returns:
        AuthService: Сервіс для роботи з аутентифікацією.
    """
    return AuthService(db)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    name="Реєстрація користувача",
    description="Додає нового користувача. Перевіряє наявність користувача з таким username або email.",
    response_description="Повертає користувача, або 409, якщо користувач з таким username або email вже існує.",
)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Реєстрація нового користувача.

    Args:
        user_data (UserCreate): Дані нового користувача (username, email, пароль).
        background_tasks (BackgroundTasks): Завдання у фон для відправки листа підтвердження.
        request (Request): Поточний HTTP-запит.
        auth_service (AuthService): Сервіс аутентифікації.

    Returns:
        UserResponse: Дані зареєстрованого користувача.
    """
    user = await auth_service.register_user(user_data)
    background_tasks.add_task(
        send_email,
        user_data.email,
        user_data.username,
        str(request.base_url),
        type_email="confirm_email",
    )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    name="Авторизація користувача",
    description="Авторизує користувача. Перевіряє наявність користувача з таким username або email.",
    response_description="Повертає access та refresh токен, або 401, якщо користувач username або email невірні.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Вхід користувача в систему.

    Args:
        form_data (OAuth2PasswordRequestForm): Дані для входу (username і пароль).
        request (Request, optional): Поточний HTTP-запит.
        auth_service (AuthService): Сервіс аутентифікації.

    Returns:
        TokenResponse: Пара токенів (access та refresh).
    """
    user = await auth_service.authenticate(form_data.username, form_data.password)
    access_token = auth_service.create_access_token(user.username)
    refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    return TokenResponse(
        access_token=access_token, token_type="bearer", refresh_token=refresh_token
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    name="Оновлення токена",
    description="Приймає refresh-токен і видає нову пару токенів: access та refresh.",
    response_description="JSON з новим access-токеном та новим refresh-токеном.",
)
async def refresh(
    refresh_token: RefreshTokenRequest,
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Оновлення токенів користувача.

    Args:
        refresh_token (RefreshTokenRequest): Дійсний refresh-токен.
        request (Request, optional): Поточний HTTP-запит.
        auth_service (AuthService): Сервіс аутентифікації.

    Returns:
        TokenResponse: Нові access- і refresh-токени.
    """
    user = await auth_service.validate_refresh_token(refresh_token.refresh_token)

    new_access_token = auth_service.create_access_token(user.username)
    new_refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    await auth_service.revoke_refresh_token(refresh_token.refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        refresh_token=new_refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    name="Вихід користувача із системи",
    description="Здійснює вихід користувача з системи. Access- і refresh-токени відкликаються та стають недійсними.",
    response_description="Повертає 204 No Content у випадку успішного виходу.",
)
async def logout(
    refresh_token: RefreshTokenRequest,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Вихід користувача із системи.

    Args:
        refresh_token (RefreshTokenRequest): Refresh-токен користувача.
        token (str): Access-токен користувача.
        auth_service (AuthService): Сервіс аутентифікації.

    Returns:
        None: Повертає 204 No Content.
    """
    await auth_service.revoke_access_token(token)
    await auth_service.revoke_refresh_token(refresh_token.refresh_token)
    return None
