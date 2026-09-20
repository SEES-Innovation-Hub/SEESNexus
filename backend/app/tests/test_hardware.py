from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.hardware import (
    Hardware,
    HardwareCategory,
    HardwareLoan,
    HardwareStatus,
    LoanStatus,
)
from app.models.user import User, UserRole
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hardware"


@pytest_asyncio.fixture
async def other_student_user(db_session: AsyncSession) -> User:
    user = User(
        full_name="Bola Student",
        email="bola@unilag.edu.ng",
        password=hash_password("StrongPass2"),
        department="EEE",
        level="300 Level",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_student_token(client: AsyncClient, other_student_user: User) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": other_student_user.email, "password": "StrongPass2"},
    )
    return resp.json()["data"]["access_token"]


async def seed_hardware(
    db: AsyncSession,
    *,
    name: str = "Oscilloscope",
    quantity: int = 3,
    status: HardwareStatus = HardwareStatus.AVAILABLE,
    added_by_id: str | None = None,
) -> Hardware:
    hardware = Hardware(
        name=name,
        description="Seeded hardware item",
        serial_number=f"SN-{name.lower().replace(' ', '-')}-{quantity}",
        category=HardwareCategory.MEASUREMENT,
        status=status,
        image_url=None,
        quantity=quantity,
        available_quantity=quantity,
        added_by_id=added_by_id or "seed-owner",
    )
    db.add(hardware)
    await db.commit()
    await db.refresh(hardware)
    return hardware


async def test_list_is_public_and_paginated(client: AsyncClient, db_session: AsyncSession):
    await seed_hardware(db_session, name="Scope A")
    await seed_hardware(db_session, name="Scope B", quantity=2)

    resp = await client.get(f"{BASE}?page=1&page_size=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["page"] == 1
    assert body["data"]["page_size"] == 1
    assert body["data"]["total"] == 2
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["name"] == "Scope A"


async def test_detail_is_public(client: AsyncClient, db_session: AsyncSession):
    item = await seed_hardware(db_session, name="Thermocouple")

    resp = await client.get(f"{BASE}/{item.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["id"] == item.id
    assert body["data"]["serial_number"] == item.serial_number


async def test_create_hardware_requires_admin_and_ignores_added_by_in_body(
    client: AsyncClient, db_session: AsyncSession, admin_user, admin_token: str, student_user
):
    resp = await client.post(
        BASE,
        json={
            "name": "Meter",
            "serial_number": "SN-METER-001",
            "category": "MEASUREMENT",
            "quantity": 4,
            "added_by_id": student_user.id,
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["added_by_id"] == admin_user.id
    assert body["data"]["available_quantity"] == 4


async def test_create_rejects_duplicate_serial_number(
    client: AsyncClient,
    admin_token: str,
    db_session: AsyncSession,
):
    await seed_hardware(db_session, name="DMM-1", quantity=2)

    resp = await client.post(
        BASE,
        json={
            "name": "DMM-2",
            "serial_number": "SN-dmm-1-2",
            "category": "MEASUREMENT",
            "quantity": 3,
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "error"


async def test_update_quantity_keeps_available_quantity_in_sync(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    item = await seed_hardware(db_session, name="DAQ", quantity=4)

    resp = await client.put(
        f"{BASE}/{item.id}",
        json={"quantity": 6},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["quantity"] == 6
    assert data["available_quantity"] == 6

    resp = await client.put(
        f"{BASE}/{item.id}",
        json={"quantity": 2},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["quantity"] == 2
    assert data["available_quantity"] == 2


async def test_delete_hardware_is_soft_delete(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_token: str,
):
    item = await seed_hardware(db_session, name="Bench Supply")

    resp = await client.delete(f"{BASE}/{item.id}", headers=auth_header(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["message"] == "Hardware item retired"

    result = await db_session.execute(select(Hardware).where(Hardware.id == item.id))
    saved = result.scalar_one()
    assert saved.status == HardwareStatus.MAINTENANCE


async def test_request_loan_happy_path_keeps_quantity_unchanged(
    client: AsyncClient, db_session: AsyncSession, student_user: User, student_token: str
):
    item = await seed_hardware(db_session, name="DAQ Box", quantity=2, added_by_id=student_user.id)

    resp = await client.post(
        f"{BASE}/{item.id}/loan",
        json={
            "purpose": "Capstone lab use",
            "expected_return_date": (
                datetime.now(timezone.utc) + timedelta(days=3)
            ).isoformat(),
        },
        headers=auth_header(student_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["status"] == "PENDING"
    assert body["data"]["borrower_id"] == student_user.id

    refreshed = await db_session.get(Hardware, item.id)
    assert refreshed.available_quantity == 2


async def test_request_loan_rejects_unavailable_or_maintenance(
    client: AsyncClient, db_session: AsyncSession, student_token: str, student_user: User
):
    unavailable = await seed_hardware(
        db_session,
        name="Unavailable Kit",
        quantity=1,
        added_by_id=student_user.id,
    )
    unavailable.available_quantity = 0
    await db_session.commit()

    resp = await client.post(
        f"{BASE}/{unavailable.id}/loan",
        json={"purpose": "Should fail"},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400

    maintenance = await seed_hardware(
        db_session,
        name="Maintenance Kit",
        quantity=2,
        status=HardwareStatus.MAINTENANCE,
        added_by_id=student_user.id,
    )
    resp = await client.post(
        f"{BASE}/{maintenance.id}/loan",
        json={"purpose": "Should fail"},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400


async def test_request_loan_rejects_duplicate_open_request(
    client: AsyncClient, db_session: AsyncSession, student_user: User, student_token: str
):
    item = await seed_hardware(db_session, name="Duplicated Kit", quantity=2, added_by_id=student_user.id)
    await client.post(
        f"{BASE}/{item.id}/loan",
        json={"purpose": "First request"},
        headers=auth_header(student_token),
    )

    resp = await client.post(
        f"{BASE}/{item.id}/loan",
        json={"purpose": "Second request"},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 400


async def test_my_loans_lists_only_current_user(
    client: AsyncClient,
    db_session: AsyncSession,
    student_user: User,
    student_token: str,
    other_student_user: User,
    other_student_token: str,
):
    hardware_a = await seed_hardware(db_session, name="Laser A", quantity=1, added_by_id=student_user.id)
    hardware_b = await seed_hardware(db_session, name="Laser B", quantity=1, added_by_id=student_user.id)

    await client.post(
        f"{BASE}/{hardware_a.id}/loan",
        json={"purpose": "mine"},
        headers=auth_header(student_token),
    )
    await client.post(
        f"{BASE}/{hardware_b.id}/loan",
        json={"purpose": "other student"},
        headers=auth_header(other_student_token),
    )

    resp = await client.get(f"{BASE}/loans/my", headers=auth_header(student_token))
    assert resp.status_code == 200
    ids = {loan["hardware_id"] for loan in resp.json()["data"]}
    assert hardware_a.id in ids
    assert hardware_b.id not in ids


async def test_return_loan_by_borrower_updates_inventory(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str,
    student_user: User,
    student_token: str,
):
    item = await seed_hardware(db_session, name="Scope Return", quantity=2, added_by_id=student_user.id)
    loan = HardwareLoan(
        hardware_id=item.id,
        borrower_id=student_user.id,
        approved_by_id=admin_user.id,
        status=LoanStatus.APPROVED,
        purpose="Need to return",
        request_date=datetime.now(timezone.utc),
        approval_date=datetime.now(timezone.utc),
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)

    item.available_quantity = 1
    await db_session.commit()

    resp = await client.put(
        f"{BASE}/loans/{loan.id}/return",
        headers=auth_header(student_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "RETURNED"

    refreshed = await db_session.get(Hardware, item.id)
    assert refreshed.available_quantity == 2


async def test_return_loan_forbidden_for_admin_or_other_student(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_token: str,
    student_token: str,
    student_user: User,
    admin_user: User,
    other_student_user: User,
    other_student_token: str,
):
    item = await seed_hardware(db_session, name="Admin Return Guard", quantity=2, added_by_id=student_user.id)
    loan = HardwareLoan(
        hardware_id=item.id,
        borrower_id=student_user.id,
        approved_by_id=admin_user.id,
        status=LoanStatus.APPROVED,
        purpose="Return guard",
        request_date=datetime.now(timezone.utc),
        approval_date=datetime.now(timezone.utc),
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)

    resp = await client.put(f"{BASE}/loans/{loan.id}/return", headers=auth_header(admin_token))
    assert resp.status_code == 403

    resp = await client.put(f"{BASE}/loans/{loan.id}/return", headers=auth_header(other_student_token))
    assert resp.status_code == 403


async def test_return_loan_rejects_pending_or_unknown(
    client: AsyncClient, db_session: AsyncSession, student_user: User, student_token: str
):
    item = await seed_hardware(db_session, name="Bad Return", quantity=2, added_by_id=student_user.id)
    loan = HardwareLoan(
        hardware_id=item.id,
        borrower_id=student_user.id,
        status=LoanStatus.PENDING,
        purpose="Not approved yet",
        request_date=datetime.now(timezone.utc),
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)

    resp = await client.put(f"{BASE}/loans/{loan.id}/return", headers=auth_header(student_token))
    assert resp.status_code == 400

    resp = await client.put(f"{BASE}/loans/does-not-exist/return", headers=auth_header(student_token))
    assert resp.status_code == 404


async def test_loan_invariant_approve_then_return_restores_quantity(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_token: str,
    student_token: str,
    student_user: User,
    admin_user: User,
):
    item = await seed_hardware(db_session, name="Quantity Restore", quantity=2, added_by_id=student_user.id)
    loan = HardwareLoan(
        hardware_id=item.id,
        borrower_id=student_user.id,
        status=LoanStatus.PENDING,
        purpose="Final check",
        request_date=datetime.now(timezone.utc),
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)

    resp = await client.put(f"/api/v1/admin/loans/{loan.id}/approve", headers=auth_header(admin_token))
    assert resp.status_code == 200
    item = await db_session.get(Hardware, item.id)
    assert item.available_quantity == 1

    resp = await client.put(f"{BASE}/loans/{loan.id}/return", headers=auth_header(student_token))
    assert resp.status_code == 200
    item = await db_session.get(Hardware, item.id)
    assert item.available_quantity == 2


async def test_rejecting_loan_does_not_change_quantity(
    client: AsyncClient, db_session: AsyncSession, admin_token: str, student_user: User
):
    item = await seed_hardware(db_session, name="Reject Guard", quantity=2, added_by_id=student_user.id)
    loan = HardwareLoan(
        hardware_id=item.id,
        borrower_id=student_user.id,
        status=LoanStatus.PENDING,
        purpose="Test reject",
        request_date=datetime.now(timezone.utc),
    )
    db_session.add(loan)
    await db_session.commit()
    await db_session.refresh(loan)

    resp = await client.put(f"/api/v1/admin/loans/{loan.id}/reject", headers=auth_header(admin_token))
    assert resp.status_code == 200

    refreshed = await db_session.get(Hardware, item.id)
    assert refreshed.available_quantity == 2
