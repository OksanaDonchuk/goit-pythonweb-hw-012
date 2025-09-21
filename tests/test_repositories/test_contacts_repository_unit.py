import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from src.entity.models import Contact, User
from src.repositories.contacts_repository import ContactRepository
from src.schemas.contacts_schema import ContactSchema, ContactUpdateSchema


@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def contact_repository(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def mock_user():
    return User(id=1)


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, mock_user):
    contact_data = ContactSchema(
        first_name="Oksana",
        last_name="Donchuk",
        email="oksana@gmail.com",
        phone="+380505555555",
        birthday=date(1980, 9, 23),
        additional_info="",
    )
    expected_contact = Contact(**contact_data.model_dump(), user=mock_user)
    mock_session.refresh.return_value = expected_contact

    result = await contact_repository.create_contact(contact_data, mock_user)

    assert result.first_name == contact_data.first_name
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_contacts(contact_repository, mock_session, mock_user):
    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_contact]
    mock_session.execute.return_value = mock_result

    result = await contact_repository.get_all_contacts(
        limit=10, offset=0, user=mock_user
    )

    assert result == [mock_contact]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repository, mock_session, mock_user):
    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    result = await contact_repository.get_contact_by_id(contact_id=1, user=mock_user)

    assert result == mock_contact
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, mock_user):
    mock_contact = Contact(id=1, user_id=mock_user.id, additional_info="студентка")
    updated_data = ContactUpdateSchema(additional_info="студентка")
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result
    mock_session.refresh.return_value = mock_contact

    result = await contact_repository.update_contact(
        contact_id=1, body=updated_data, user=mock_user
    )

    assert result.additional_info == "студентка"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_remove_contact(contact_repository, mock_session, mock_user):
    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    result = await contact_repository.remove_contact(contact_id=1, user=mock_user)

    assert result == mock_contact
    mock_session.delete.assert_called_once_with(mock_contact)
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_contact_by_query(contact_repository, mock_session, mock_user):

    mock_contact = Contact(id=1, user_id=mock_user.id)
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_contact]
    mock_session.execute.return_value = mock_result

    result = await contact_repository.get_contact_by_query(
        query="Oksana", user=mock_user
    )

    assert result == [mock_contact]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contacts_by_upcoming_birthdays(
    contact_repository, mock_session, mock_user
):

    mock_contact = Contact(id=1, user_id=mock_user.id, birthday=date(1980, 2, 9))
    mock_result = Mock()
    mock_result.scalars.return_value.all.return_value = [mock_contact]
    mock_session.execute.return_value = mock_result

    result = await contact_repository.get_contacts_by_upcoming_birthdays(user=mock_user)

    assert result == [mock_contact]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_email_or_phone(contact_repository, mock_session, mock_user):
    mock_contact = Contact(
        id=1, user_id=mock_user.id, email="oksana@gmail.com", phone="123"
    )
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    result = await contact_repository.get_by_email_or_phone(
        "oksana@gmail.com", "123", mock_user
    )

    assert result == mock_contact
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_email_or_phone_returns_none(
    contact_repository, mock_session, mock_user
):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await contact_repository.get_by_email_or_phone(
        "none@gmail.com", "000", mock_user
    )

    assert result is None


@pytest.mark.asyncio
async def test_exists_other_with_email_or_phone_true(
    contact_repository, mock_session, mock_user
):
    mock_contact = Contact(id=2, user_id=mock_user.id, email="oksana@gmail.com")
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_contact
    mock_session.execute.return_value = mock_result

    result = await contact_repository.exists_other_with_email_or_phone(
        user=mock_user, contact_id=1, email="oksana@gmail.com"
    )

    assert result is True
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_exists_other_with_email_or_phone_false(
    contact_repository, mock_session, mock_user
):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await contact_repository.exists_other_with_email_or_phone(
        user=mock_user, contact_id=1, email="notfound@gmail.com"
    )

    assert result is False


# --- ДОДАТКОВІ НЕГАТИВНІ ТЕСТИ ---


@pytest.mark.asyncio
async def test_update_contact_returns_none_if_not_found(
    contact_repository, mock_session, mock_user
):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await contact_repository.update_contact(
        contact_id=999, body=ContactUpdateSchema(additional_info="test"), user=mock_user
    )

    assert result is None


@pytest.mark.asyncio
async def test_remove_contact_none_if_not_found(
    contact_repository, mock_session, mock_user
):
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await contact_repository.remove_contact(contact_id=999, user=mock_user)

    assert result is None


@pytest.mark.asyncio
async def test_get_contact_by_query_empty(contact_repository, mock_session, mock_user):
    result = await contact_repository.get_contact_by_query("", mock_user)
    assert result == []
