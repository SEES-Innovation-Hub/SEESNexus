import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hardware import Hardware, HardwareCategory, HardwareLoan, LoanStatus
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


# --- /admin/dashboard ---


async def test_dashboard_happy_path(client: AsyncClient, admin_token: str, student_user):
    resp = await client.get("/api/v1/admin/dashboard", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()["data"]
    # admin_user + student_user fixtures both exist by the time this runs
    assert data["total_users"] >= 2
    assert data["students"] >= 1
    assert data["admins"] >= 1


async def test_dashboard_forbidden_for_student(client: AsyncClient, student_token: str):
    resp = await client.get("/api/v1/admin/dashboard", headers=auth_header(student_token))
    assert resp.status_code == 403
    assert resp.json()["status"] == "error"


async def test_dashboard_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/admin/dashboard")
    assert resp.status_code == 401


# --- /admin/users ---


async def test_list_users_happy_path(client: AsyncClient, admin_token: str, student_user):
    resp = await client.get("/api/v1/admin/users", headers=auth_header(admin_token))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()["data"]]
    assert student_user.email in emails


async def test_list_users_forbidden_for_student(client: AsyncClient, student_token: str):
    resp = await client.get("/api/v1/admin/users", headers=auth_header(student_token))
    assert resp.status_code == 403


# --- /admin/users/{id}/role ---


async def test_change_role_happy_path(client: AsyncClient, admin_token: str, student_user):
    resp = await client.put(
        f"/api/v1/admin/users/{student_user.id}/role",
        json={"role": "CONTRIBUTOR"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["role"] == "CONTRIBUTOR"


async def test_change_role_404_for_unknown_user(client: AsyncClient, admin_token: str):
    resp = await client.put(
        "/api/v1/admin/users/does-not-exist/role",
        json={"role": "ADMIN"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


async def test_change_role_forbidden_for_student(client: AsyncClient, student_token: str, student_user):
    resp = await client.put(
        f"/api/v1/admin/users/{student_user.id}/role",
        json={"role": "ADMIN"},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 403


async def test_admin_cannot_change_own_role(
    client: AsyncClient, admin_token: str, admin_user
):
    resp = await client.put(
        f"/api/v1/admin/users/{admin_user.id}/role",
        json={"role": "STUDENT"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "error"


# --- DELETE /admin/users/{id} (deactivate) ---


async def test_deactivate_user_happy_path(client: AsyncClient, admin_token: str, student_user):
    resp = await client.delete(
        f"/api/v1/admin/users/{student_user.id}", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200

    # The deactivated student can no longer log in.
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": student_user.email, "password": "StrongPass1"}
    )
    assert login_resp.status_code == 401


async def test_deactivate_user_forbidden_for_student(client: AsyncClient, student_token: str, admin_user):
    resp = await client.delete(
        f"/api/v1/admin/users/{admin_user.id}", headers=auth_header(student_token)
    )
    assert resp.status_code == 403


async def test_admin_cannot_deactivate_self(
    client: AsyncClient, admin_token: str, admin_user
):
    resp = await client.delete(
        f"/api/v1/admin/users/{admin_user.id}", headers=auth_header(admin_token)
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "error"

    # Admin is still able to call protected endpoints afterwards.
    follow_up = await client.get("/api/v1/admin/dashboard", headers=auth_header(admin_token))
    assert follow_up.status_code == 200


# --- PUT /admin/users/{id}/activate ---


async def test_activate_user_restores_login(
    client: AsyncClient, admin_token: str, student_user
):
    # Deactivate first so there is something to reactivate.
    await client.delete(
        f"/api/v1/admin/users/{student_user.id}", headers=auth_header(admin_token)
    )

    resp = await client.put(
        f"/api/v1/admin/users/{student_user.id}/activate",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is True

    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": student_user.email, "password": "StrongPass1"}
    )
    assert login_resp.status_code == 200


async def test_activate_unknown_user_404(client: AsyncClient, admin_token: str):
    resp = await client.put(
        "/api/v1/admin/users/does-not-exist/activate",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


async def test_activate_user_forbidden_for_student(
    client: AsyncClient, student_token: str, student_user
):
    resp = await client.put(
        f"/api/v1/admin/users/{student_user.id}/activate",
        headers=auth_header(student_token),
    )
    assert resp.status_code == 403


# --- Loans: /admin/loans, approve, reject, return ---


@pytest.fixture
def hardware_item():
    return None  # placeholder; real item created in async fixture below


@pytest.fixture
async def pending_loan(db_session: AsyncSession, student_user) -> HardwareLoan:
    hardware = Hardware(
        name="Oscilloscope",
        serial_number="OSC-001",
        category=HardwareCategory.MEASUREMENT,
        quantity=2,
        available_quantity=2,
        added_by_id=student_user.id,
    )
    db_session.add(hardware)
    await db_session.commit()
    await db_session.refresh(hardware)

    loan = HardwareLoan(
        hardware_id=hardware.id,
        borrower_id=student_user.id,
        status=LoanStatus.PENDING,
        purpose="Final year project testing",
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)
    return loan


async def test_list_loans_happy_path(client: AsyncClient, admin_token: str, pending_loan: HardwareLoan):
    resp = await client.get("/api/v1/admin/loans", headers=auth_header(admin_token))
    assert resp.status_code == 200
    loan_ids = [loan["id"] for loan in resp.json()["data"]]
    assert pending_loan.id in loan_ids


async def test_approve_loan_happy_path(
    client: AsyncClient, admin_token: str, db_session: AsyncSession, pending_loan: HardwareLoan
):
    resp = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/approve", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "APPROVED"

    hardware = await db_session.get(Hardware, pending_loan.hardware_id)
    assert hardware.available_quantity == 1  # decremented from 2


async def test_approve_loan_twice_fails(client: AsyncClient, admin_token: str, pending_loan: HardwareLoan):
    first = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/approve", headers=auth_header(admin_token)
    )
    assert first.status_code == 200

    second = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/approve", headers=auth_header(admin_token)
    )
    assert second.status_code == 400


async def test_reject_loan_happy_path(client: AsyncClient, admin_token: str, pending_loan: HardwareLoan):
    resp = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/reject", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "REJECTED"


async def test_approve_loan_forbidden_for_student(
    client: AsyncClient, student_token: str, pending_loan: HardwareLoan
):
    resp = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/approve", headers=auth_header(student_token)
    )
    assert resp.status_code == 403


async def test_approve_loan_404_for_unknown_loan(client: AsyncClient, admin_token: str):
    resp = await client.put(
        "/api/v1/admin/loans/does-not-exist/approve", headers=auth_header(admin_token)
    )
    assert resp.status_code == 404


async def test_return_loan_happy_path(
    client: AsyncClient, admin_token: str, db_session: AsyncSession, pending_loan: HardwareLoan
):
    # Approve first so there is an APPROVED loan to return.
    approve = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/approve", headers=auth_header(admin_token)
    )
    assert approve.status_code == 200

    resp = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/return", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "RETURNED"

    hardware = await db_session.get(Hardware, pending_loan.hardware_id)
    assert hardware.available_quantity == 2  # back to the original stock


async def test_return_loan_rejects_non_approved(
    client: AsyncClient, admin_token: str, pending_loan: HardwareLoan
):
    # pending_loan is PENDING, not APPROVED, so returning should fail.
    resp = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/return", headers=auth_header(admin_token)
    )
    assert resp.status_code == 400


async def test_return_loan_forbidden_for_student(
    client: AsyncClient, student_token: str, pending_loan: HardwareLoan
):
    resp = await client.put(
        f"/api/v1/admin/loans/{pending_loan.id}/return", headers=auth_header(student_token)
    )
    assert resp.status_code == 403
