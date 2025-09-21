import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, Mock

from src.entity.models import RefreshToken
from src.repositories.refresh_token_repository import RefreshTokenRepository


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
def refresh_token_repository(mock_session):
    return RefreshTokenRepository(mock_session)


@pytest.mark.asyncio
async def test_get_by_token_hash(refresh_token_repository, mock_session):
    token_hash = "test_hash"
    mock_token = RefreshToken(token_hash=token_hash)
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = mock_token
    mock_session.execute.return_value = mock_result

    result = await refresh_token_repository.get_by_token_hash(token_hash)

    assert result == mock_token
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_token(refresh_token_repository, mock_session):
    token_hash = "test_hash"
    current_time = datetime.now()
    expired_at = current_time + timedelta(days=1)
    mock_token = RefreshToken(
        token_hash=token_hash, expired_at=expired_at, revoked_at=None
    )
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = mock_token
    mock_session.execute.return_value = mock_result

    result = await refresh_token_repository.get_active_token(token_hash, current_time)

    assert result == mock_token
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_save_token(refresh_token_repository, mock_session):
    user_id = 1
    token_hash = "test_hash"
    expired_at = datetime.now() + timedelta(days=1)
    ip_address = "127.0.0.1"
    user_agent = "test_agent"
    mock_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expired_at=expired_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    mock_session.refresh.return_value = mock_token

    result = await refresh_token_repository.save_token(
        user_id=user_id,
        token_hash=token_hash,
        expired_at=expired_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    assert result.user_id == mock_token.user_id
    assert result.token_hash == mock_token.token_hash
    assert result.expired_at == mock_token.expired_at
    assert result.ip_address == mock_token.ip_address
    assert result.user_agent == mock_token.user_agent
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_revoke_token(refresh_token_repository, mock_session):
    mock_token = RefreshToken(
        token_hash="test_hash",
        expired_at=datetime.now() + timedelta(days=1),
        revoked_at=None,
    )

    await refresh_token_repository.revoke_token(mock_token)

    assert mock_token.revoked_at is not None
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_token_hash_not_found(refresh_token_repository, mock_session):
    token_hash = "non_existing_hash"
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await refresh_token_repository.get_by_token_hash(token_hash)

    assert result is None
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_token_expired(refresh_token_repository, mock_session):
    token_hash = "expired_hash"
    current_time = datetime.now()
    expired_at = current_time - timedelta(days=1)
    mock_token = RefreshToken(
        token_hash=token_hash, expired_at=expired_at, revoked_at=None
    )

    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await refresh_token_repository.get_active_token(token_hash, current_time)

    assert result is None
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_token_revoked(refresh_token_repository, mock_session):
    token_hash = "revoked_hash"
    current_time = datetime.now()
    expired_at = current_time + timedelta(days=1)
    revoked_at = datetime.now()
    mock_token = RefreshToken(
        token_hash=token_hash, expired_at=expired_at, revoked_at=revoked_at
    )

    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await refresh_token_repository.get_active_token(token_hash, current_time)

    assert result is None
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_revoke_token_commits_and_sets_revoked_at(
    refresh_token_repository, mock_session
):
    mock_token = RefreshToken(
        token_hash="test_hash",
        expired_at=datetime.now() + timedelta(days=1),
        revoked_at=None,
    )

    before = mock_token.revoked_at
    await refresh_token_repository.revoke_token(mock_token)
    after = mock_token.revoked_at

    assert before is None
    assert after is not None
    mock_session.commit.assert_called_once()
