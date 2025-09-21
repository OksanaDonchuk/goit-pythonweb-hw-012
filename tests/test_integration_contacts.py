import pytest


BASE_CONTACT = {
    "first_name": "Oksana",
    "last_name": "Donchuk",
    "email": "oksana@example.com",
    "phone": "+380501112233",
    "birthday": "1980-09-23",
    "additional_info": "Студентка університету",
}


@pytest.fixture
def contact(client, get_tokens):
    """Фікстура: створює контакт перед тестом і видаляє його після."""
    access_token = get_tokens["user_access"]

    response = client.post(
        "/api/contacts/",
        json=BASE_CONTACT,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201, response.text
    contact = response.json()

    yield contact

    client.delete(
        f"/api/contacts/{contact['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def test_create_contact(client, get_tokens):
    """Тестуємо створення нового контакту."""
    access_token = get_tokens["user_access"]

    payload = BASE_CONTACT.copy()
    payload["email"] = "unique@example.com"
    payload["phone"] = "+380509999999"

    response = client.post(
        "/api/contacts/",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["phone"] == payload["phone"]
    assert data["birthday"] == payload["birthday"]
    assert data["additional_info"] == payload["additional_info"]
    assert data["first_name"] == payload["first_name"]
    assert data["last_name"] == payload["last_name"]
    assert "id" in data

    client.delete(
        f"/api/contacts/{data['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )


def test_create_duplicate_contact(client, get_tokens, contact):
    """Дублювання email/телефону → 409."""
    access_token = get_tokens["user_access"]

    response = client.post(
        "/api/contacts/",
        json=BASE_CONTACT,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 409
    assert "вже існує" in response.json()["detail"]


def test_get_all_contacts(client, get_tokens, contact):
    access_token = get_tokens["user_access"]
    response = client.get(
        "/api/contacts/",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert any(c["id"] == contact["id"] for c in data)


def test_get_contact_by_id(client, get_tokens, contact):
    access_token = get_tokens["user_access"]
    response = client.get(
        f"/api/contacts/{contact['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contact["id"]


def test_update_contact(client, get_tokens, contact):
    access_token = get_tokens["user_access"]
    payload = {"additional_info": "Оновлена інформація"}
    response = client.put(
        f"/api/contacts/{contact['id']}",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["additional_info"] == "Оновлена інформація"


def test_delete_contact(client, get_tokens):
    """Створюємо і видаляємо контакт."""
    access_token = get_tokens["user_access"]

    payload = BASE_CONTACT.copy()
    payload["email"] = "delete@example.com"
    payload["phone"] = "+380508888888"

    response = client.post(
        "/api/contacts/",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201
    contact_id = response.json()["id"]

    response = client.delete(
        f"/api/contacts/{contact_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 204
