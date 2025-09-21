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
    name="Отримання даних поточного користувача",
    description="Отримує інформацію про автентифікованого користувача на основі переданого токена доступу. Дані беруться з кешу Redis або з бази даних, якщо користувача в кеші немає.",
    response_description="Повертає інформацію про поточного користувача",
)
@limiter.limit("5/minute")
async def me(
    request: Request,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Повертає дані автентифікованого користувача.

    Args:
        request (Request): Об’єкт запиту FastAPI (для rate limiting).
        token (str): Access-токен користувача.
        auth_service (AuthService): Сервіс автентифікації.

    Returns:
        UserResponse: Поточний користувач із кешу Redis або БД.
    """
    return await auth_service.get_current_user(token)


@router.get(
    "/confirmed_email/{token}",
    name="Підтвердження електронної пошти",
    description="Виконує підтвердження електронної пошти користувача за допомогою токена.",
    response_description="Повертає повідомлення про успішне підтвердження пошти або повідомлення, що пошта вже підтверджена.",
)
async def confirmed_email(
    token: str, user_service: UserService = Depends(get_user_service)
):
    """
    Підтверджує електронну пошту користувача за допомогою токена.

    - **token**: унікальний токен підтвердження, отриманий користувачем на email.
    - Якщо токен валідний і користувач існує — його поле `confirmed` оновлюється на True.
    - Якщо пошта вже підтверджена, повертається відповідне повідомлення.
    - У разі невалідного токена або відсутності користувача повертається помилка 400.
    """
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


@router.post(
    "/request_email",
    name="Запит на повторне підтвердження електронної пошти",
    description="Надсилає повторний лист із підтвердженням електронної пошти користувачу. "
    "Якщо пошта вже підтверджена, повертається повідомлення про це. "
    "Якщо пошта ще не підтверджена — на вказану адресу відправляється новий лист із токеном підтвердження.",
    response_description="Повідомлення про статус підтвердження або інструкцію перевірити пошту.",
)
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """
    Відправляє повторний лист для підтвердження email.

    Args:
        body (RequestEmail): Об’єкт зі значенням email користувача.
        background_tasks (BackgroundTasks): Черга для асинхронної відправки листа.
        request (Request): Об’єкт запиту FastAPI.
        user_service (UserService): Сервіс для роботи з користувачами.

    Returns:
        dict: Повідомлення про статус підтвердження.
    """
    user = await user_service.get_user_by_email(str(body.email))

    if user.confirmed:
        return {"message": messages.email_has_confirmed}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": messages.check_email}


@router.patch(
    "/avatar",
    response_model=UserResponse,
    name="Оновлення аватару",
    description="Оновлює аватар користувача у хмарному сервісі."
    "Доступ дозволений лише користувачам із роллю admin."
    "Файл зображення завантажується через форму (тип multipart/form-data)",
    response_description="Дані користувача з оновленим URL аватару.",
)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Оновлює аватар користувача у хмарному сервісі.

    Args:
        file (UploadFile): Файл зображення у форматі multipart/form-data.
        user (User): Авторизований користувач з роллю admin.
        user_service (UserService): Сервіс користувачів.

    Returns:
        UserResponse: Дані користувача з новим URL аватару.
    """
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user


@router.post(
    "/request_password_reset",
    name="Запит на скидання паролю",
    description="Приймає email користувача і створює фонове завдання на відправку листа",
    response_description="Повідомлення про відправку інструкцій на пошту.",
)
async def request_password_reset(
    body: ResetPasswordRequestSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """
    Ставитиме у фон завдання на відправлення листа зі скиданням пароля.

    Токен створюється всередині send_email (type_email="reset_password").
    Повертаємо однакове повідомлення, аби не розкривати існування email.

    Args:
        body (ResetPasswordRequestSchema): Email користувача.
        background_tasks (BackgroundTasks): Черга для відправки листа.
        request (Request): Об’єкт запиту FastAPI.
        user_service (UserService): Сервіс користувачів.

    Returns:
        dict: Повідомлення про відправку інструкцій.
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


@router.post(
    "/reset_password",
    name="Скидання паролю",
    description="Приймає токен для підтвердження запиту на скидання паролю та новий пароль.",
    response_description="Повідомлення про успішне скидання паролю.",
)
async def reset_password(
    body: ResetPasswordSchema,
    user_service: UserService = Depends(get_user_service),
):
    """
    Скидає пароль користувача.

    Args:
        body (ResetPasswordSchema): Об’єкт із токеном скидання паролю та новим паролем.
        user_service (UserService): Сервіс для роботи з користувачами.

    Returns:
        dict: Повідомлення про успішне скидання пароля.
    """
    return await user_service.reset_password(body.token, body.new_password)
