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
    category: HardwareCategory = HardwareCategory.MEASUREMENT,
    added_by_id: str | None = None,
) -> Hardware:
    if added_by_id is None:
        user = User(
            full_name="Seed Owner",
            email=(
                "seed-owner-"
                f"{datetime.now(timezone.utc).isoformat(timespec='microseconds')}"
                "@unilag.edu.ng"
            ),
            password=hash_password("StrongPass1"),
            department="EEE",
            level="Staff",
            role=UserRole.ADMIN,
        )
        db.add(user)
        await db.flush()
        added_by_id = user.id

    hardware = Hardware(
        name=name,
        description="Seeded hardware item",
        serial_number=f"SN-{name.lower().replace(' ', '-')}-{quantity}",
        category=category,
        status=status,
        image_url=None,
        quantity=quantity,
        available_quantity=quantity,
        added_by_id=added_by_id,
    )
    db.add(hardware)
    await db.commit()
    await db.refresh(hardware)
    return hardware


async def test_list_requires_auth_and_paginates(
    client: AsyncClient, db_session: AsyncSession, student_token: str
):
    await seed_hardware(db_session, name="Scope A")
    await seed_hardware(db_session, name="Scope B", quantity=2)

    # Members only: anonymous callers are rejected.
    anon = await client.get(f"{BASE}?page=1&page_size=1")
    assert anon.status_code == 401

    resp = await client.get(f"{BASE}?page=1&page_size=1", headers=auth_header(student_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["page"] == 1
    assert body["data"]["page_size"] == 1
    assert body["data"]["total"] == 2
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["name"] == "Scope A"


async def test_detail_requires_auth(
    client: AsyncClient, db_session: AsyncSession, student_token: str
):
    item = await seed_hardware(db_session, name="Thermocouple")

    anon = await client.get(f"{BASE}/{item.id}")
    assert anon.status_code == 401

    resp = await client.get(f"{BASE}/{item.id}", headers=auth_header(student_token))
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


async def test_admin_return_loan_updates_inventory(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str,
    student_user: User,
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
        f"/api/v1/admin/loans/{loan.id}/return",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "RETURNED"

    refreshed = await db_session.get(Hardware, item.id)
    assert refreshed.available_quantity == 2


async def test_admin_return_loan_forbidden_for_students(
    client: AsyncClient,
    db_session: AsyncSession,
    student_token: str,
    student_user: User,
    admin_user: User,
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

    resp = await client.put(
        f"/api/v1/admin/loans/{loan.id}/return",
        headers=auth_header(student_token),
    )
    assert resp.status_code == 403


async def test_admin_return_loan_rejects_pending_or_unknown(
    client: AsyncClient, db_session: AsyncSession, student_user: User, admin_token: str
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

    resp = await client.put(
        f"/api/v1/admin/loans/{loan.id}/return", headers=auth_header(admin_token)
    )
    assert resp.status_code == 400

    resp = await client.put(
        "/api/v1/admin/loans/does-not-exist/return", headers=auth_header(admin_token)
    )
    assert resp.status_code == 404


async def test_loan_invariant_approve_then_return_restores_quantity(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_token: str,
    student_user: User,
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

    resp = await client.put(f"/api/v1/admin/loans/{loan.id}/return", headers=auth_header(admin_token))
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


async def seed_loan(
    db: AsyncSession,
    *,
    hardware: Hardware,
    borrower: User,
    status: LoanStatus = LoanStatus.PENDING,
    approved_by_id: str | None = None,
) -> HardwareLoan:
    loan = HardwareLoan(
        hardware_id=hardware.id,
        borrower_id=borrower.id,
        approved_by_id=approved_by_id,
        status=status,
        purpose="Seeded loan",
        request_date=datetime.now(timezone.utc),
        approval_date=datetime.now(timezone.utc) if approved_by_id else None,
    )
    db.add(loan)
    await db.commit()
    await db.refresh(loan)
    return loan


# --- Auth failures: every protected endpoint rejects an anonymous caller ---
# §3.14's Definition of Done is happy-path *plus auth-failure* per endpoint.


async def test_protected_endpoints_reject_anonymous_callers(
    client: AsyncClient, db_session: AsyncSession, student_user: User
):
    item = await seed_hardware(db_session, name="Anon Guard", quantity=1)

    calls = [
        client.get(BASE),
        client.get(f"{BASE}/{item.id}"),
        client.post(BASE, json={}),
        client.put(f"{BASE}/{item.id}", json={"name": "x"}),
        client.delete(f"{BASE}/{item.id}"),
        client.post(f"{BASE}/{item.id}/loan", json={"purpose": "x"}),
        client.get(f"{BASE}/loans/my"),
    ]
    for call in calls:
        resp = await call
        assert resp.status_code == 401, resp.request.url


async def test_admin_only_endpoints_reject_students(
    client: AsyncClient, db_session: AsyncSession, student_token: str
):
    item = await seed_hardware(db_session, name="Role Guard", quantity=1)

    resp = await client.put(
        f"{BASE}/{item.id}", json={"name": "Renamed"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 403

    resp = await client.delete(f"{BASE}/{item.id}", headers=auth_header(student_token))
    assert resp.status_code == 403


async def test_unknown_ids_are_404(client: AsyncClient, admin_token: str, student_token: str):
    assert (
        await client.get(f"{BASE}/does-not-exist", headers=auth_header(student_token))
    ).status_code == 404

    resp = await client.put(
        f"{BASE}/does-not-exist", json={"name": "x"}, headers=auth_header(admin_token)
    )
    assert resp.status_code == 404

    resp = await client.delete(f"{BASE}/does-not-exist", headers=auth_header(admin_token))
    assert resp.status_code == 404

    resp = await client.post(
        f"{BASE}/does-not-exist/loan", json={"purpose": "x"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 404


# --- List shaping ---


async def test_list_filters_and_ordering(
    client: AsyncClient, db_session: AsyncSession, student_token: str
):
    await seed_hardware(db_session, name="Zeta Meter", category=HardwareCategory.MEASUREMENT)
    await seed_hardware(db_session, name="Alpha Board", category=HardwareCategory.MICROCONTROLLER)
    await seed_hardware(
        db_session, name="Mid Resistor", category=HardwareCategory.COMPONENT,
        status=HardwareStatus.MAINTENANCE,
    )

    headers = auth_header(student_token)
    resp = await client.get(BASE, headers=headers)
    names = [item["name"] for item in resp.json()["data"]["items"]]
    assert names == sorted(names), "inventory is ordered by name ascending"

    resp = await client.get(BASE, params={"category": "MICROCONTROLLER"}, headers=headers)
    items = resp.json()["data"]["items"]
    assert [item["name"] for item in items] == ["Alpha Board"]

    resp = await client.get(BASE, params={"status": "MAINTENANCE"}, headers=headers)
    items = resp.json()["data"]["items"]
    assert [item["name"] for item in items] == ["Mid Resistor"]


async def test_page_size_is_clamped_server_side(
    client: AsyncClient, db_session: AsyncSession, student_token: str
):
    await seed_hardware(db_session, name="Clamp Probe")

    resp = await client.get(
        BASE, params={"page_size": 5000}, headers=auth_header(student_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["page_size"] == 100


# --- Stock adjustment guard ---


async def test_quantity_cannot_drop_below_units_on_loan(
    client: AsyncClient, db_session: AsyncSession, admin_token: str
):
    item = await seed_hardware(db_session, name="Stock Guard", quantity=3)
    # Two units are out on loan.
    item.available_quantity = 1
    await db_session.commit()

    resp = await client.put(f"{BASE}/{item.id}", json={"quantity": 1}, headers=auth_header(admin_token))
    assert resp.status_code == 400

    refreshed = await db_session.get(Hardware, item.id)
    assert refreshed.quantity == 3
    assert refreshed.available_quantity == 1


# --- Derived status: the half that never existed before the return path ---


async def test_last_unit_flips_to_borrowed_and_back_on_return(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str,
    student_user: User,
):
    item = await seed_hardware(db_session, name="Sole Unit", quantity=1, added_by_id=admin_user.id)
    loan = await seed_loan(db_session, hardware=item, borrower=student_user)

    resp = await client.put(
        f"/api/v1/admin/loans/{loan.id}/approve", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200

    refreshed = await db_session.get(Hardware, item.id)
    await db_session.refresh(refreshed)
    assert refreshed.available_quantity == 0
    assert refreshed.status is HardwareStatus.BORROWED

    resp = await client.put(
        f"/api/v1/admin/loans/{loan.id}/return", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200

    await db_session.refresh(refreshed)
    assert refreshed.available_quantity == 1
    assert refreshed.status is HardwareStatus.AVAILABLE


async def test_maintenance_status_survives_approval_and_return(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_token: str,
    student_user: User,
):
    """An item on the repair bench stays there regardless of units moving.

    Guards the early return in loans._apply_availability_delta. The old inline
    code in admin.py would have flipped this item to BORROWED on approval.
    """
    item = await seed_hardware(db_session, name="Bench Unit", quantity=1, added_by_id=admin_user.id)
    loan = await seed_loan(db_session, hardware=item, borrower=student_user)

    item.status = HardwareStatus.MAINTENANCE
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/admin/loans/{loan.id}/approve", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200

    await db_session.refresh(item)
    assert item.available_quantity == 0
    assert item.status is HardwareStatus.MAINTENANCE

    resp = await client.put(
        f"/api/v1/admin/loans/{loan.id}/return", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200

    await db_session.refresh(item)
    assert item.available_quantity == 1
    assert item.status is HardwareStatus.MAINTENANCE


# --- Loan history ---


async def test_my_loans_includes_closed_loans(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    student_user: User,
    student_token: str,
):
    """§5.4 calls this endpoint "my loan history".

    Filtering it to open states would erase a student's record of everything
    they ever borrowed and gave back.
    """
    returned_item = await seed_hardware(db_session, name="Closed Loan Item", quantity=1)
    rejected_item = await seed_hardware(db_session, name="Refused Loan Item", quantity=1)

    await seed_loan(
        db_session,
        hardware=returned_item,
        borrower=student_user,
        status=LoanStatus.RETURNED,
        approved_by_id=admin_user.id,
    )
    await seed_loan(
        db_session,
        hardware=rejected_item,
        borrower=student_user,
        status=LoanStatus.REJECTED,
        approved_by_id=admin_user.id,
    )

    resp = await client.get(f"{BASE}/loans/my", headers=auth_header(student_token))
    assert resp.status_code == 200
    states = {loan["status"] for loan in resp.json()["data"]}
    assert states == {"RETURNED", "REJECTED"}


async def test_loan_response_carries_hardware_name(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    student_user: User,
    student_token: str,
    admin_token: str,
):
    """Loan rows surface the item's human name alongside its id.

    The frontend lists loans without a second round trip per row, so
    hardware_name must be present on every loan response.
    """
    item = await seed_hardware(db_session, name="Named Scope", quantity=1, added_by_id=admin_user.id)
    loan = await seed_loan(db_session, hardware=item, borrower=student_user)

    resp = await client.get(f"{BASE}/loans/my", headers=auth_header(student_token))
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert any(row["id"] == loan.id and row["hardware_name"] == "Named Scope" for row in rows)

    resp = await client.get("/api/v1/admin/loans", headers=auth_header(admin_token))
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert any(row["id"] == loan.id and row["hardware_name"] == "Named Scope" for row in rows)

    resp = await client.put(
        f"/api/v1/admin/loans/{loan.id}/approve", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["hardware_name"] == "Named Scope"


async def test_retired_item_cannot_be_borrowed(
    client: AsyncClient, db_session: AsyncSession, admin_token: str, student_token: str
):
    item = await seed_hardware(db_session, name="Retired Scope", quantity=2)

    resp = await client.delete(f"{BASE}/{item.id}", headers=auth_header(admin_token))
    assert resp.status_code == 200

    resp = await client.post(
        f"{BASE}/{item.id}/loan", json={"purpose": "too late"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 400
