"""Tests for the /auth routes (src/celiacwriteoff/backend/routers/auth.py).

This file starts with one fully-worked example, test_signup_success, that
exercises the whole fixture chain end to end: the temp database, the
TestClient wired to it, and a request that goes all the way through
password hashing, user creation, and session-cookie creation.

More cases to add here as a learning exercise (see the plan for the full
list): weak password -> 422, mismatched confirm_password -> 422, duplicate
email -> 409, login success/failure, login attempts getting logged,
/auth/me requiring a session, forgot-password's enumeration-safe response,
and the full reset-password flow (valid token, expired/used token).
"""


def test_signup_success(client):
    response = client.post(
        "/auth/signup",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@example.com",
            "password": "Str0ng!Passw0rd",
            "confirm_password": "Str0ng!Passw0rd",
            "recaptcha_token": "",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "ada@example.com"
    assert body["full_name"] == "Ada Lovelace"
    assert body["is_admin"] is False
    assert "id" in body
    assert "created_at" in body

    assert "session_token" in response.cookies
