"""Login API tests, including JWT issuance."""

from __future__ import annotations

from sqlalchemy import select

from app.auth.jwt import decode_token
from app.models.user import User

_PASSWORD = "StrongPassword123!"


def _register(client, email="user@example.com", password=_PASSWORD):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )


def _login(client, email="user@example.com", password=_PASSWORD):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_correct_credentials_succeed(api_client):
    assert _register(api_client).status_code == 201
    response = _login(api_client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["is_active"] is True
    payload = decode_token(body["access_token"])
    assert payload["sub"] == str(body["user"]["id"])
    assert "exp" in payload
    assert "password" not in body
    assert "hashed_password" not in body
    assert "hashed_password" not in body["user"]
    assert "password" not in body["user"]


def test_wrong_password_is_unauthorized(api_client):
    assert _register(api_client, email="wrongpw@example.com").status_code == 201
    response = _login(api_client, email="wrongpw@example.com", password="WrongPass123!")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
    assert "access_token" not in response.json()


def test_unknown_email_same_error_as_wrong_password(api_client):
    unknown = _login(api_client, email="nobody@example.com", password=_PASSWORD)
    assert _register(api_client, email="known@example.com").status_code == 201
    wrong = _login(api_client, email="known@example.com", password="WrongPass123!")
    assert unknown.status_code == 401
    assert wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"]
    assert unknown.json()["detail"] == "Invalid email or password."
    assert "access_token" not in unknown.json()
    assert "access_token" not in wrong.json()


def test_inactive_user_rejected(api_client, db_session):
    email = "inactive@example.com"
    assert _register(api_client, email=email).status_code == 201
    user = db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    user.is_active = False
    db_session.flush()

    response = _login(api_client, email=email)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_response_never_contains_password(api_client):
    _register(api_client, email="safe-login@example.com")
    response = _login(api_client, email="safe-login@example.com")
    raw = response.text.lower()
    assert "hashed_password" not in raw
    body = response.json()
    assert "password" not in body
    assert "password" not in body["user"]


def test_protected_route_without_token_is_401(api_client):
    response = api_client.get("/api/v1/companies")
    assert response.status_code == 401


def test_protected_route_with_token_succeeds(auth_client):
    response = auth_client.get("/api/v1/companies")
    assert response.status_code == 200, response.text
