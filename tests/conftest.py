import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from main import app
from src.core.depend_service import get_current_user
from src.entity.models import Base, User, UserRole, RefreshToken
from src.database.db import get_db
from src.services.auth_services import AuthService

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_admin = {
    "username": "admin_user",
    "email": "admin@example.com",
    "password": "123456789",
}
test_user = {
    "username": "regular_user",
    "email": "regular@example.com",
    "password": "123456789",
}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal() as session:
            auth_service = AuthService(session)

            hash_password_admin = auth_service._hash_password(test_admin["password"])
            admin = User(
                username=test_admin["username"],
                email=test_admin["email"],
                hash_password=hash_password_admin,
                confirmed=True,
                avatar="https://twitter.com/gravatar",
                role=UserRole.ADMIN,
            )

            hash_password_user = auth_service._hash_password(test_user["password"])
            regular_user = User(
                username=test_user["username"],
                email=test_user["email"],
                hash_password=hash_password_user,
                confirmed=True,
                avatar="https://twitter.com/gravatar",
                role=UserRole.USER,
            )

            session.add_all([admin, regular_user])
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_tokens():
    """
    Генерує access та refresh токени для адміна і звичайного юзера.
    Повертає dict із ключами: admin_access, admin_refresh, user_access, user_refresh
    """
    async with TestingSessionLocal() as session:
        auth_service = AuthService(session)

        tokens = {}

        # --- Admin ---
        tokens["admin_access"] = auth_service.create_access_token(
            test_admin["username"]
        )
        tokens["admin_refresh"] = await auth_service.create_refresh_token(
            user_id=1, ip_address="127.0.0.1", user_agent="pytest"
        )

        # --- User ---
        tokens["user_access"] = auth_service.create_access_token(test_user["username"])
        tokens["user_refresh"] = await auth_service.create_refresh_token(
            user_id=2, ip_address="127.0.0.1", user_agent="pytest"
        )

    return tokens


from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def mock_redis():
    """
    Автоматично замінює redis_client у всіх тестах,
    щоб уникнути підключення до реального Redis.
    """
    with patch("src.services.auth_services.redis_client") as redis_mock:
        redis_mock.exists = AsyncMock(return_value=False)
        redis_mock.setex = AsyncMock(return_value=True)
        redis_mock.get = AsyncMock(return_value=None)
        yield redis_mock


@pytest.fixture(autouse=True)
def override_current_user(client):
    async def _get_current_user_override():
        async with TestingSessionLocal() as session:
            return await session.get(User, 2)  # наш regular_user з init_models

    app.dependency_overrides[get_current_user] = _get_current_user_override
    yield
    app.dependency_overrides.pop(get_current_user, None)
