import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta, declarative_base
from sqlalchemy import Column, Integer, String

from src.repositories.base_repository import BaseRepository

Base: DeclarativeMeta = declarative_base()


class DummyModel(Base):
    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True)
    name = Column(String)


@pytest.fixture
def dummy_instance():
    return DummyModel(id=1, name="Test")


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repository(mock_session):
    return BaseRepository(session=mock_session, model=DummyModel)


@pytest.mark.asyncio
async def test_get_all(repository, mock_session, dummy_instance):
    scalars_mock = Mock()
    scalars_mock.all.return_value = [dummy_instance]

    mock_result = Mock()
    mock_result.scalars.return_value = scalars_mock

    mock_session.execute.return_value = mock_result

    result = await repository.get_all()

    mock_session.execute.assert_called_once()
    assert result == [dummy_instance]


@pytest.mark.asyncio
async def test_get_all_if_no_records(repository, mock_session):
    scalars_mock = Mock()
    scalars_mock.all.return_value = []

    mock_result = Mock()
    mock_result.scalars.return_value = scalars_mock

    mock_session.execute.return_value = mock_result

    result = await repository.get_all()

    assert result == []


@pytest.mark.asyncio
async def test_get_by_id(repository, mock_session, dummy_instance):
    scalars_mock = Mock()
    scalars_mock.first.return_value = dummy_instance

    mock_result = Mock()
    mock_result.scalars.return_value = scalars_mock

    mock_session.execute.return_value = mock_result

    result = await repository.get_by_id(1)

    mock_session.execute.assert_called_once()
    assert result == dummy_instance


@pytest.mark.asyncio
async def test_get_by_id_returns_none_if_not_found(repository, mock_session):
    scalars_mock = Mock()
    scalars_mock.first.return_value = None

    mock_result = Mock()
    mock_result.scalars.return_value = scalars_mock

    mock_session.execute.return_value = mock_result

    result = await repository.get_by_id(999)

    assert result is None


@pytest.mark.asyncio
async def test_create(repository, mock_session, dummy_instance):
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.return_value = None

    result = await repository.create(dummy_instance)

    mock_session.add.assert_called_once_with(dummy_instance)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(dummy_instance)
    assert result == dummy_instance


@pytest.mark.asyncio
async def test_update(repository, mock_session, dummy_instance):
    mock_session.commit.return_value = None
    mock_session.refresh.return_value = None

    result = await repository.update(dummy_instance)

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(dummy_instance)
    assert result == dummy_instance


@pytest.mark.asyncio
async def test_delete(repository, mock_session, dummy_instance):
    mock_session.delete.return_value = None
    mock_session.commit.return_value = None

    result = await repository.delete(dummy_instance)

    mock_session.delete.assert_called_once_with(dummy_instance)
    mock_session.commit.assert_called_once()
    assert result is None
