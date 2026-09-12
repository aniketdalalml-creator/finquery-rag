"""Registration API tests. No login or JWT."""

from __future__ import annotations

from sqlalchemy import select

from app.auth.passwords import verify_password
from app.models.user import User


def _register(client, email="user@example.com", password="StrongPassword123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )


def test_successful_registration(api_client):
    response = _register(api_client)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["is_active"] is True
    assert isinstance(body["id"], int)
    assert "password" not in body
    assert "hashed_password" not in body


def test_invalid_email(api_client):
    response = _register(api_client, email="not-an-email")
    assert response.status_code == 422


def test_weak_password(api_client):
    response = _register(api_client, email="weak@example.com", password="short")
    assert response.status_code == 422


def test_empty_password(api_client):
    response = _register(api_client, email="empty@example.com", password="")
    assert response.status_code == 422


def test_duplicate_email(api_client):
    first = _register(api_client, email="dup@example.com")
    assert first.status_code == 201
    second = _register(api_client, email="dup@example.com")
    assert second.status_code == 409
    assert "hashed_password" not in second.json()


def test_duplicate_email_case_insensitive(api_client):
    assert _register(api_client, email="Casey@example.com").status_code == 201
    again = _register(api_client, email="casey@example.com")
    assert again.status_code == 409


def test_password_is_stored_hashed(api_client, db_session):
    plain = "StrongPassword123!"
    response = _register(api_client, email="hashed@example.com", password=plain)
    assert response.status_code == 201

    user = db_session.scalar(
        select(User).where(User.email == "hashed@example.com")
    )
    assert user is not None
    assert user.hashed_password != plain
    assert user.hashed_password.startswith("$2")
    assert verify_password(plain, user.hashed_password)


def test_response_never_contains_hashed_password(api_client):
    response = _register(api_client, email="safe@example.com")
    raw = response.text.lower()
    assert "hashed_password" not in raw
    assert "password" not in response.json()
