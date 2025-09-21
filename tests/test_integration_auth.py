from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from tests.conftest import test_user


def patch_email(monkeypatch):
    """Глушимо реальну відправку листів."""
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email_services.send_email", mock_send_email)


def login_user(client: TestClient, username: str, password: str):
    """Синхронний логін через TestClient (OAuth2PasswordRequestForm)."""
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )


def get_tokens_for_user(client: TestClient, username: str, password: str):
    """Отримати пару токенів для валідного користувача."""
    response = login_user(client, username, password)
    assert response.status_code == 201, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, f"No access_token in response: {data}"
    assert "refresh_token" in data, f"No refresh_token in response: {data}"
    return data["access_token"], data["refresh_token"]


def test_register(client, monkeypatch):
    """Реєстрація нового користувача (не test_user/test_user2)."""
    patch_email(monkeypatch)
    payload = {
        "username": "NewUser",
        "email": "newuser@example.com",
        "password": "newpassword123",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "hash_password" not in data
    assert "avatar" in data


def test_repeat_register_username(client, monkeypatch):
    """Такий самий username -> 409, повідомлення: user_exists."""
    patch_email(monkeypatch)
    payload = {
        "username": test_user["username"],
        "email": "other_email@example.com",
        "password": "somepassword",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Такий користувач вже зареєстрований"


def test_repeat_register_email(client, monkeypatch):
    """Такий самий email -> 409, повідомлення: mail_exists."""
    patch_email(monkeypatch)
    payload = {
        "username": "OtherUser",
        "email": test_user["email"],
        "password": "somepassword",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "Користувач з таким e-mail вже зареєстрований"


def test_login_admin_user(client):
    """Логін існуючого користувача (ADMIN з conftest)."""
    response = login_user(client, test_user["username"], test_user["password"])
    assert response.status_code == 201, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_wrong_password_login(client):
    """Неправильний пароль -> 401 authenticate_wrong_user."""
    response = login_user(client, test_user["username"], "wrong_password")
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Невірне ім’я або пароль"


def test_wrong_username_login(client):
    """Невідомий username -> 401 authenticate_wrong_user."""
    response = login_user(client, "unknown_user", test_user["password"])
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "Невірне ім’я або пароль"


def test_validation_error_login(client):
    """Відсутній username у формі -> 422."""
    response = client.post("/api/auth/login", data={"password": test_user["password"]})
    assert response.status_code == 422, response.text
    assert "detail" in response.json()


def test_refresh_token(client):
    """Оновлення пари токенів валідним refresh-токеном."""
    _, refresh_token = get_tokens_for_user(
        client, test_user["username"], test_user["password"]
    )
    response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] != refresh_token


def test_logout(client):
    """Вихід: відкликання access і refresh; Redis замокаємо."""
    with patch("src.services.auth_services.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        access_token, refresh_token = get_tokens_for_user(
            client, test_user["username"], test_user["password"]
        )
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204, response.text
