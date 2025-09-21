import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, Mock

from src.entity.models import User
from src.repositories.user_repository import UserRepository
from src.schemas.user_schema import UserCreate


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_get_by_username(user_repository, mock_session):
    username = "testuser"
    mock_user = User(username=username)
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await user_repository.get_by_username(username)

    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session):
    email = "testuser@gmail.com"
    mock_user = User(email=email)
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await user_repository.get_user_by_email(email)

    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session):
    user_data = UserCreate(
        username="testuser", email="testuser@gmail.com", password="123456789"
    )
    hashed_password = "hashed_password"
    avatar = "avatar_url"
    mock_user = User(
        username=user_data.username,
        email=user_data.email,
        hash_password=hashed_password,
        avatar=avatar,
    )
    mock_session.refresh.return_value = mock_user

    result = await user_repository.create_user(user_data, hashed_password, avatar)

    assert result.username == mock_user.username
    assert result.email == mock_user.email
    assert result.hash_password == mock_user.hash_password
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_confirmed_email(user_repository, mock_session):
    email = "testuser@gmail.com"
    mock_user = User(email=email, confirmed=False)
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    await user_repository.confirmed_email(email)

    assert mock_user.confirmed is True
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session):
    email = "testuser@gmail.com"
    new_url = "new_avatar_url"
    mock_user = User(email=email, avatar="old_url")
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    mock_session.refresh.return_value = mock_user

    result = await user_repository.update_avatar_url(email, new_url)

    assert result.avatar == new_url
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_update_password(user_repository, mock_session):
    email = "testuser@gmail.com"
    new_password = "new_hashed_password"
    mock_user = User(email=email, hash_password="old_password")
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result
    mock_session.refresh.return_value = mock_user

    result = await user_repository.update_password(email, new_password)

    assert result.hash_password == new_password
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_user)


@pytest.mark.asyncio
async def test_get_by_username_not_found(user_repository, mock_session):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await user_repository.get_by_username("unknown")

    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_repository, mock_session):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await user_repository.get_user_by_email("nope@gmail.com")

    assert result is None


@pytest.mark.asyncio
async def test_update_password_user_not_found(user_repository, mock_session):
    email = "missing@gmail.com"
    new_password = "new_password"
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(AttributeError):
        await user_repository.update_password(email, new_password)


@pytest.mark.asyncio
async def test_update_avatar_url_user_not_found(user_repository, mock_session):
    email = "missing@gmail.com"
    new_url = "new_avatar"
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(AttributeError):
        await user_repository.update_avatar_url(email, new_url)
