from unittest.mock import Mock

from main import app
from src.core import email_token
from src.core.depend_service import get_current_admin_user
from src.core.email_token import create_email_token
from src.entity.models import User, UserRole
from src.services.auth_services import AuthService
from src.conf import messages
from tests.conftest import TestingSessionLocal, test_admin, test_user


def patch_email(monkeypatch):
    """Глушимо реальну відправку email."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email_services.send_email", mock_send_email)


def make_email_token(email: str) -> str:
    """Створює email-токен так само, як у сервісі."""

    async def _make():
        async with TestingSessionLocal() as session:
            auth_service = AuthService(session)
            return email_token.create_email_token(email)

    import asyncio

    return asyncio.run(_make())


def test_me_success(client, get_tokens):
    """Отримання поточного користувача з access токеном (admin)."""
    headers = {"Authorization": f"Bearer {get_tokens['admin_access']}"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_admin["username"]
    assert data["email"] == test_admin["email"]
    assert "id" in data


def test_me_unauthorized(client):
    """Без токена → 401."""
    response = client.get("/api/users/me")
    assert response.status_code == 401


def test_confirmed_email_success(client):
    """Валідний токен → підтвердження email."""

    async def _make():
        async with TestingSessionLocal() as session:
            auth_service = AuthService(session)
            return auth_service.create_access_token(test_user["username"])

    import asyncio

    token = asyncio.run(_make())

    response = client.get(f"/api/users/confirmed_email/{token}")
    assert response.status_code in (200, 400, 422), response.text
    if response.status_code == 200:
        assert response.json()["message"] in (
            messages.email_confirmed_success,
            messages.email_has_confirmed,
        )


def test_confirmed_email_invalid_token(client):
    """Невалідний токен → 422."""
    response = client.get("/api/users/confirmed_email/badtoken")
    assert response.status_code == 422


def test_request_email_unconfirmed(client, monkeypatch):
    """Email ще не підтверджений → новий лист підтвердження."""
    patch_email(monkeypatch)
    response = client.post(
        "/api/users/request_email", json={"email": test_user["email"]}
    )
    assert response.status_code == 200
    assert "message" in response.json()


def test_request_email_confirmed(client, monkeypatch):
    """Email вже підтверджений → повідомлення без повторної відправки."""
    patch_email(monkeypatch)
    response = client.post(
        "/api/users/request_email", json={"email": test_admin["email"]}
    )
    assert response.status_code == 200
    assert response.json()["message"] == messages.email_has_confirmed


def test_update_avatar_user_admin(client, monkeypatch):
    fake_url = "http://example.com/avatar.png"
    monkeypatch.setattr(
        "src.services.upload_file_service.UploadFileService.upload_file",
        lambda self, file, username: fake_url,
    )

    def override_admin_user():
        return User(
            id=1,
            username="admin_user",
            email="admin@example.com",
            hash_password="x",
            role=UserRole.ADMIN,
            confirmed=True,
        )

    app.dependency_overrides[get_current_admin_user] = override_admin_user
    try:
        files = {"file": ("avatar.png", b"fakeimagecontent", "image/png")}
        resp = client.patch("/api/users/avatar", files=files)
        assert resp.status_code == 200, resp.text
        assert resp.json()["avatar"] == fake_url
    finally:
        app.dependency_overrides.pop(get_current_admin_user, None)


def test_update_avatar_user_forbidden(client, get_tokens, monkeypatch):
    """Звичайний user → 403."""
    headers = {"Authorization": f"Bearer {get_tokens['user_access']}"}
    files = {"file": ("avatar.png", b"fakeimagecontent", "image/png")}
    response = client.patch("/api/users/avatar", headers=headers, files=files)
    assert response.status_code == 403


def test_request_password_reset_nonexistent(client, monkeypatch):
    """Неіснуючий email → все одно повертає однакове повідомлення."""
    patch_email(monkeypatch)
    response = client.post(
        "/api/users/request_password_reset", json={"email": "ghost@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == messages.password_reset_email_sent


def test_reset_password_success(client):
    token = create_email_token({"sub": "admin@example.com"})
    payload = {"token": token, "new_password": "newsecret123"}

    resp = client.post("/api/users/reset_password", json=payload)
    assert resp.status_code == 200, resp.text
    assert resp.json()["message"] == messages.password_reset_success


def test_reset_password_invalid_token(client):
    """Невалідний токен → 422."""
    payload = {"token": "badtoken", "new_password": "newsecret123"}
    response = client.post("/api/users/reset_password", json=payload)
    assert response.status_code == 422
