from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hardware import Hardware, HardwareCategory, HardwareStatus
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/hardware"


async def seed_hardware(db: AsyncSession, *, name: str = "Oscilloscope", quantity: int = 3, status: HardwareStatus = HardwareStatus.AVAILABLE, added_by_id: str | None = None) -> Hardware:
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


async def test_create_rejects_duplicate_serial_number(client: AsyncClient, admin_token: str, db_session: AsyncSession):
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


async def test_delete_hardware_is_soft_delete(client: AsyncClient, db_session: AsyncSession, admin_token: str):
    item = await seed_hardware(db_session, name="Bench Supply")

    resp = await client.delete(f"{BASE}/{item.id}", headers=auth_header(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["message"] == "Hardware item retired"

    result = await db_session.execute(select(Hardware).where(Hardware.id == item.id))
    saved = result.scalar_one()
    assert saved.status == HardwareStatus.MAINTENANCE
