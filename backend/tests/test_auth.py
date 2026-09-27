"""Auth flow tests."""

from __future__ import annotations

from tests.conftest import count_audit, register


def test_register_valid(client, db_session) -> None:  # type: ignore[no-untyped-def]
    body = register(client, email="newuser@example.com")
    assert body["user"]["email"] == "newuser@example.com"
    assert body["organization"]["id"]
    # HttpOnly cookie set
    set_cookie = client.cookies.get("access_token")
    assert set_cookie
    raw = client.post(
        "/api/v1/auth/register",
        json={"name": "X", "email": "x@example.com", "password": "StrongPass123!"},
    )
    assert "httponly" in raw.headers.get("set-cookie", "").lower()
    assert count_audit(db_session, "user.register") == 2


def test_register_invalid_email(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Bob", "email": "not-an-email", "password": "StrongPass123!"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_register_weak_password(client) -> None:  # type: ignore[no-untyped-def]
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "weak"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "weak_password"
    assert "password" in body["error"]["fields"]


def test_register_duplicate_email(client) -> None:  # type: ignore[no-untyped-def]
    register(client, email="dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Dup", "email": "dup@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_taken"


def test_login_success_sets_cookie(client, db_session) -> None:  # type: ignore[no-untyped-def]
    register(client, email="login@example.com", password="StrongPass123!")
    client.cookies.clear()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    assert client.cookies.get("access_token")
    assert "httponly" in response.headers.get("set-cookie", "").lower()
    assert count_audit(db_session, "auth.login.success") == 1


def test_login_failure_generic_message(client, db_session) -> None:  # type: ignore[no-untyped-def]
    register(client, email="victim@example.com", password="StrongPass123!")
    # Wrong password for an existing user...
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "victim@example.com", "password": "WrongPass123!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password."
    # ...and an unknown user get the identical message.
    response2 = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "WrongPass123!"},
    )
    assert response2.status_code == 401
    assert response2.json()["error"]["message"] == "Invalid email or password."
    assert count_audit(db_session, "auth.login.failure") == 2


def test_me_returns_user_and_org(client) -> None:  # type: ignore[no-untyped-def]
    body = register(client, email="me@example.com")
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "me@example.com"
    assert data["organization"]["id"] == body["organization"]["id"]
    assert data["role"] == "admin"


def test_logout_clears_cookie(client, db_session) -> None:  # type: ignore[no-untyped-def]
    register(client, email="logout@example.com")
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    # After logout the cookie is cleared: /me must now be unauthorized.
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert count_audit(db_session, "auth.logout") == 1


def test_unauthorized_without_cookie(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
