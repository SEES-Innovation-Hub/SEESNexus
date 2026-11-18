"""Code attempt limits, rate limits, and password reset."""
import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models.user import User
from app.services import otp, rate_limit
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

SEND = "/api/v1/notify/send-code"
VERIFY = "/api/v1/notify/verify-code"
LOGIN = "/api/v1/auth/login"
FORGOT = "/api/v1/auth/forgot-password"
RESET = "/api/v1/auth/reset-password"


async def _send(client: AsyncClient, email: str) -> str:
    resp = await client.post(SEND, json={"email": email})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["debug_code"]


def _wrong(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"


# --- email code attempts ---


async def test_code_locks_after_five_wrong_tries(client: AsyncClient):
    email = "guess@unilag.edu.ng"
    code = await _send(client, email)

    for attempt in range(1, otp.MAX_ATTEMPTS + 1):
        resp = await client.post(VERIFY, json={"email": email, "code": _wrong(code)})
        assert resp.status_code == 400
        expected = "Too many wrong tries" if attempt == otp.MAX_ATTEMPTS else "isn't right"
        assert expected in resp.json()["message"]

    # Even the right code is dead now.
    locked = await client.post(VERIFY, json={"email": email, "code": code})
    assert locked.status_code == 400
    assert "Too many wrong tries" in locked.json()["message"]

    # A fresh code starts over.
    fresh = await _send(client, email)
    assert (await client.post(VERIFY, json={"email": email, "code": fresh})).status_code == 200


async def test_a_new_code_replaces_the_old_one(client: AsyncClient):
    email = "twice@unilag.edu.ng"
    first = await _send(client, email)
    second = await _send(client, email)
    if first != second:
        old = await client.post(VERIFY, json={"email": email, "code": first})
        assert old.status_code == 400
    assert (await client.post(VERIFY, json={"email": email, "code": second})).status_code == 200
    # Used codes can't be verified twice.
    again = await client.post(VERIFY, json={"email": email, "code": second})
    assert "expired or was already used" in again.json()["message"]


# --- rate limits ---


async def test_login_is_limited_per_email_and_a_real_login_resets_it(
    client: AsyncClient, student_user: User
):
    bad = {"email": student_user.email, "password": "wrong-password"}
    good = {"email": student_user.email, "password": "StrongPass1"}

    for _ in range(rate_limit.LOGIN_PER_EMAIL.limit - 1):
        assert (await client.post(LOGIN, json=bad)).status_code == 401
    # The owner gets in before the limit, which clears their count...
    assert (await client.post(LOGIN, json=good)).status_code == 200
    # ...so they have the full allowance again.
    for _ in range(rate_limit.LOGIN_PER_EMAIL.limit):
        assert (await client.post(LOGIN, json=bad)).status_code == 401

    blocked = await client.post(LOGIN, json=good)
    assert blocked.status_code == 429
    assert blocked.json()["status"] == "error"
    assert "Too many attempts" in blocked.json()["message"]
    assert int(blocked.headers["Retry-After"]) > 0


async def test_login_is_limited_per_ip_across_accounts(client: AsyncClient):
    for i in range(rate_limit.LOGIN_PER_IP.limit):
        resp = await client.post(LOGIN, json={"email": f"nobody{i}@unilag.edu.ng", "password": "x" * 8})
        assert resp.status_code == 401
    resp = await client.post(LOGIN, json={"email": "another@unilag.edu.ng", "password": "x" * 8})
    assert resp.status_code == 429


async def test_send_code_is_limited_per_email_and_per_ip(client: AsyncClient):
    for _ in range(rate_limit.SEND_CODE_PER_EMAIL.limit):
        await _send(client, "inbox@unilag.edu.ng")
    flood = await client.post(SEND, json={"email": "inbox@unilag.edu.ng"})
    assert flood.status_code == 429

    # Different addresses from the same IP hit the per-IP cap.
    sent = rate_limit.SEND_CODE_PER_EMAIL.limit + 1  # the refused call above counted per IP
    for i in range(rate_limit.SEND_CODE_PER_IP.limit - sent):
        await _send(client, f"spray{i}@unilag.edu.ng")
    spray = await client.post(SEND, json={"email": "one-more@unilag.edu.ng"})
    assert spray.status_code == 429


async def test_verify_code_is_limited_per_ip(client: AsyncClient):
    for i in range(rate_limit.VERIFY_CODE_PER_IP.limit):
        await client.post(VERIFY, json={"email": f"v{i}@unilag.edu.ng", "code": "000000"})
    resp = await client.post(VERIFY, json={"email": "last@unilag.edu.ng", "code": "000000"})
    assert resp.status_code == 429


async def test_admin_key_check_is_limited(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_REGISTRATION_KEY", "k" * 30)
    for _ in range(rate_limit.ADMIN_KEY_PER_IP.limit):
        assert (
            await client.post("/api/v1/auth/admin-key/check", json={"admin_key": "guess"})
        ).status_code == 403
    assert (
        await client.post("/api/v1/auth/admin-key/check", json={"admin_key": "guess"})
    ).status_code == 429


async def test_client_ip_uses_trusted_proxy_entries_only(monkeypatch):
    from starlette.requests import Request

    def make(header: str | None) -> Request:
        headers = [(b"x-forwarded-for", header.encode())] if header else []
        return Request({"type": "http", "headers": headers, "client": ("10.0.0.5", 1234)})

    # No trusted proxy: the TCP peer, whatever the header claims.
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 0)
    assert rate_limit.client_ip(make("1.2.3.4")) == "10.0.0.5"

    # One proxy (Render): the address it appended, not the client-written ones before it.
    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 1)
    assert rate_limit.client_ip(make("6.6.6.6, 203.0.113.7")) == "203.0.113.7"
    assert rate_limit.client_ip(make(None)) == "10.0.0.5"


# --- forgot / reset password ---


async def test_forgot_password_says_the_same_thing_for_unknown_addresses(
    client: AsyncClient, student_user: User
):
    known = await client.post(FORGOT, json={"email": student_user.email})
    unknown = await client.post(FORGOT, json={"email": "ghost@unilag.edu.ng"})
    assert known.status_code == unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]
    # No code exists for the unknown address (dev-only debug_code shows it).
    assert "debug_code" not in unknown.json()["data"]


async def test_reset_password_end_to_end(client: AsyncClient, student_user: User):
    sent = await client.post(FORGOT, json={"email": student_user.email})
    code = sent.json()["data"]["debug_code"]

    # A registration code can't be used to reset a password.
    reg_code = await _send(client, student_user.email)
    wrong_kind = await client.post(
        RESET, json={"email": student_user.email, "code": reg_code, "new_password": "BrandNew123"}
    )
    if reg_code != code:
        assert wrong_kind.status_code == 400

    ok = await client.post(
        RESET, json={"email": student_user.email, "code": code, "new_password": "BrandNew123"}
    )
    assert ok.status_code == 200

    # The old password is gone; the new one works.
    assert (
        await client.post(LOGIN, json={"email": student_user.email, "password": "StrongPass1"})
    ).status_code == 401
    assert (
        await client.post(LOGIN, json={"email": student_user.email, "password": "BrandNew123"})
    ).status_code == 200

    # The code can't be used twice.
    again = await client.post(
        RESET, json={"email": student_user.email, "code": code, "new_password": "Another123"}
    )
    assert again.status_code == 400


async def test_old_tokens_are_refused_after_a_reset(client: AsyncClient, student_user: User, db_session):
    """Deterministic version of the sign-out check: backdate the old token's iat."""
    from datetime import datetime, timedelta, timezone

    from app.core.security import TokenType, _create_token

    old_access = _create_token(student_user.id, TokenType.ACCESS, timedelta(minutes=30))
    old_refresh = _create_token(student_user.id, TokenType.REFRESH, timedelta(days=7))
    student_user.password_changed_at = datetime.now(timezone.utc) + timedelta(seconds=5)
    await db_session.commit()

    me = await client.get("/api/v1/auth/me", headers=auth_header(old_access))
    assert me.status_code == 401
    assert me.json()["message"] == "Your password was changed. Please log in again."
    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 401

    # A token minted after the change works.
    student_user.password_changed_at = datetime.now(timezone.utc) - timedelta(seconds=5)
    await db_session.commit()
    fresh = _create_token(student_user.id, TokenType.ACCESS, timedelta(minutes=30))
    assert (await client.get("/api/v1/auth/me", headers=auth_header(fresh))).status_code == 200


async def test_reset_code_locks_after_five_wrong_tries(client: AsyncClient, student_user: User):
    code = (await client.post(FORGOT, json={"email": student_user.email})).json()["data"]["debug_code"]
    for _ in range(otp.MAX_ATTEMPTS):
        await client.post(
            RESET, json={"email": student_user.email, "code": _wrong(code), "new_password": "BrandNew123"}
        )
    locked = await client.post(
        RESET, json={"email": student_user.email, "code": code, "new_password": "BrandNew123"}
    )
    assert locked.status_code == 400
    assert "Too many wrong tries" in locked.json()["message"]


async def test_reset_rejects_a_short_password(client: AsyncClient, student_user: User):
    code = (await client.post(FORGOT, json={"email": student_user.email})).json()["data"]["debug_code"]
    resp = await client.post(RESET, json={"email": student_user.email, "code": code, "new_password": "short"})
    assert resp.status_code == 422
