from fastapi import (
    APIRouter,
    Depends,
    Request,
    BackgroundTasks,
    status,
    HTTPException,
    UploadFile,
    File,
)
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.conf import messages
from src.conf.config import settings
from src.core.depend_service import (
    get_auth_service,
    get_user_service,
    get_current_user,
    get_current_admin_user,
)
from src.core.email_token import get_email_from_token
from src.entity.models import User
from src.schemas.email_schema import RequestEmail
from src.schemas.password_schema import ResetPasswordSchema, ResetPasswordRequestSchema
from src.schemas.user_schema import UserResponse
from src.services.auth_services import AuthService, oauth2_scheme
from src.services.email_services import send_email
from src.services.upload_file_service import UploadFileService
from src.services.user_services import UserService

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me",
    response_model=UserResponse,
    name="Отримання поточного користувача",
    description="Не більше 5 запитів в хвилину",
)
@limiter.limit("5/minute")
async def me(
    request: Request,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.get_current_user(token)


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str, user_service: UserService = Depends(get_user_service)
):
    email = get_email_from_token(token)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": messages.email_has_confirmed}
    await user_service.confirmed_email(email)
    return {"message": messages.email_confirmed_success}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    user = await user_service.get_user_by_email(str(body.email))

    if user.confirmed:
        return {"message": messages.email_has_confirmed}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": messages.check_email}


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user


@router.post("/request_password_reset")
async def request_password_reset(
    body: ResetPasswordRequestSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """
    Ставитиме у фон завдання на відправку листа зі скиданням паролю.

    Токен створюється всередині send_email (type_email="reset_password").
    Повертаємо однакове повідомлення, аби не розкривати існування email.
    """
    user = await user_service.get_user_by_email(str(body.email))
    if user:
        background_tasks.add_task(
            send_email,
            email=user.email,
            username=user.username,
            host=str(request.base_url),
            type_email="reset_password",
        )

    return {"message": messages.password_reset_email_sent}


@router.post("/reset_password")
async def reset_password(
    body: ResetPasswordSchema,
    user_service: UserService = Depends(get_user_service),
):
    """
    Приймає токен та новий пароль, скидає пароль користувача.
    """
    return await user_service.reset_password(body.token, body.new_password)
