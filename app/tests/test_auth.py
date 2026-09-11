import pytest
from httpx import AsyncClient

from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


async def _register_new_user(client: AsyncClient, email: str = "newbie@unilag.edu.ng") -> dict:
    send_resp = await client.post("/api/v1/notify/send-code", json={"email": email})
    code = send_resp.json()["data"]["debug_code"]

    verify_resp = await client.post("/api/v1/notify/verify-code", json={"email": email, "code": code})
    assert verify_resp.status_code == 200

    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "New Bie",
            "email": email,
            "password": "SuperSecret1",
            "department": "EEE",
            "level": "200 Level",
            "verification_code": code,
        },
    )
    return register_resp


# --- /notify/send-code & /notify/verify-code ---


async def test_send_code_happy_path(client: AsyncClient):
    resp = await client.post("/api/v1/notify/send-code", json={"email": "someone@unilag.edu.ng"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "debug_code" in body["data"]


async def test_verify_code_rejects_wrong_code(client: AsyncClient):
    await client.post("/api/v1/notify/send-code", json={"email": "someone@unilag.edu.ng"})
    resp = await client.post(
        "/api/v1/notify/verify-code", json={"email": "someone@unilag.edu.ng", "code": "000000"}
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "error"


# --- /auth/register ---


async def test_register_happy_path(client: AsyncClient):
    resp = await _register_new_user(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["email"] == "newbie@unilag.edu.ng"
    assert body["data"]["role"] == "STUDENT"
    assert "password" not in body["data"]


async def test_register_fails_without_otp_verification(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "No OTP",
            "email": "noOtp@unilag.edu.ng",
            "password": "SuperSecret1",
            "department": "EEE",
            "verification_code": "123456",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "error"


async def test_register_fails_on_duplicate_email(client: AsyncClient):
    first = await _register_new_user(client, email="dupe@unilag.edu.ng")
    assert first.status_code == 201

    # Re-verify a fresh code for the same (now-registered) email, then try again.
    send_resp = await client.post("/api/v1/notify/send-code", json={"email": "dupe@unilag.edu.ng"})
    code = send_resp.json()["data"]["debug_code"]
    await client.post("/api/v1/notify/verify-code", json={"email": "dupe@unilag.edu.ng", "code": code})

    second = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Dupe Two",
            "email": "dupe@unilag.edu.ng",
            "password": "SuperSecret1",
            "department": "EEE",
            "verification_code": code,
        },
    )
    assert second.status_code == 409


# --- /auth/login ---


async def test_login_happy_path(client: AsyncClient, student_user):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": student_user.email, "password": "StrongPass1"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


async def test_login_fails_with_wrong_password(client: AsyncClient, student_user):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": student_user.email, "password": "WrongPassword"}
    )
    assert resp.status_code == 401
    assert resp.json()["status"] == "error"


async def test_login_fails_for_unknown_email(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "ghost@unilag.edu.ng", "password": "whatever123"}
    )
    assert resp.status_code == 401


# --- /auth/refresh ---


async def test_refresh_happy_path(client: AsyncClient, student_user):
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": student_user.email, "password": "StrongPass1"}
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["data"]["access_token"]


async def test_refresh_rejects_access_token_used_as_refresh(client: AsyncClient, student_token: str):
    # An access token is not a valid refresh token — the type claim must be checked.
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": student_token})
    assert resp.status_code == 401


async def test_refresh_rejects_garbage_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


# --- /auth/validate/token ---


async def test_validate_token_happy_path(client: AsyncClient, student_token: str):
    resp = await client.get("/api/v1/auth/validate/token", headers=auth_header(student_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["valid"] is True


async def test_validate_token_fails_without_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/validate/token")
    assert resp.status_code == 401


# --- /auth/me ---


async def test_get_me_happy_path(client: AsyncClient, student_token: str, student_user):
    resp = await client.get("/api/v1/auth/me", headers=auth_header(student_token))
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == student_user.email


async def test_get_me_fails_with_bad_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers=auth_header("garbage.token.here"))
    assert resp.status_code == 401


async def test_update_me_happy_path(client: AsyncClient, student_token: str):
    resp = await client.put(
        "/api/v1/auth/me", json={"bio": "Robotics enthusiast"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["bio"] == "Robotics enthusiast"


async def test_update_me_fails_without_auth(client: AsyncClient):
    resp = await client.put("/api/v1/auth/me", json={"bio": "hi"})
    assert resp.status_code == 401
