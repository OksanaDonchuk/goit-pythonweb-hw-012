import pytest
from unittest.mock import AsyncMock

from src.conf import messages
from src.database import db


def test_healthchecker_ok(client):
    resp = client.get("/api/healthchecker")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data == {"message": "Welcome to FastAPI!"}


@pytest.mark.asyncio
async def test_healthchecker_db_error(client, monkeypatch):
    async def fake_get_db():
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("DB down")
        yield mock_session

    client.app.dependency_overrides[db.get_db] = fake_get_db

    resp = client.get("/api/healthchecker")
    assert resp.status_code == 500
    assert resp.json()["detail"] == messages.db_conn_error

    client.app.dependency_overrides.pop(db.get_db, None)
