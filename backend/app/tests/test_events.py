from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.events import EventRegistration
from app.models.user import User
from app.tests.conftest import auth_header

BASE = "/api/v1/events"


def event_payload(**overrides) -> dict:
    now = datetime.now(timezone.utc)
    payload = {
        "title": "Annual Hackathon",
        "description": "Build useful tools for the campus community.",
        "event_type": "HACKATHON",
        "location": "Innovation Hub",
        "is_virtual": False,
        "start_date": (now + timedelta(days=3)).isoformat(),
        "end_date": (now + timedelta(days=3, hours=4)).isoformat(),
        "registration_deadline": (now + timedelta(days=2)).isoformat(),
        "max_participants": 2,
    }
    payload.update(overrides)
    return payload


async def create_event(client: AsyncClient, admin_token: str, **overrides) -> dict:
    response = await client.post(BASE, json=event_payload(**overrides), headers=auth_header(admin_token))
    assert response.status_code == 201, response.text
    return response.json()["data"]


@pytest.mark.asyncio
async def test_list_events_is_public_and_paginated(client: AsyncClient, admin_token: str):
    await create_event(client, admin_token)
    response = await client.get(f"{BASE}?page=1&page_size=10")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["data"]["total"] == 1


@pytest.mark.asyncio
async def test_get_event_is_public(client: AsyncClient, admin_token: str):
    event = await create_event(client, admin_token)
    response = await client.get(f"{BASE}/{event['id']}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == event["id"]


@pytest.mark.asyncio
async def test_get_unknown_event_returns_enveloped_404(client: AsyncClient):
    response = await client.get(f"{BASE}/missing-event")
    assert response.status_code == 404
    assert response.json() == {"status": "error", "message": "Event not found", "data": None}


@pytest.mark.asyncio
async def test_create_event_admin_only(client: AsyncClient, admin_token: str, student_token: str):
    response = await client.post(BASE, json=event_payload(), headers=auth_header(admin_token))
    assert response.status_code == 201
    forbidden = await client.post(BASE, json=event_payload(), headers=auth_header(student_token))
    assert forbidden.status_code == 403
    unauthenticated = await client.post(BASE, json=event_payload())
    assert unauthenticated.status_code == 401


@pytest.mark.asyncio
async def test_update_event_admin_only(client: AsyncClient, admin_token: str, student_token: str):
    event = await create_event(client, admin_token)
    response = await client.put(
        f"{BASE}/{event['id']}", json={"title": "Updated title"}, headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated title"
    assert (
        await client.put(
            f"{BASE}/{event['id']}", json={"title": "Nope"}, headers=auth_header(student_token)
        )
    ).status_code == 403
    assert (await client.put(f"{BASE}/{event['id']}", json={"title": "Nope"})).status_code == 401


@pytest.mark.asyncio
async def test_delete_event_soft_deletes_and_preserves_registration(
    client: AsyncClient, db_session, admin_token: str, student_token: str, student_user: User
):
    event = await create_event(client, admin_token)
    registration = await client.post(
        f"{BASE}/{event['id']}/register", headers=auth_header(student_token)
    )
    assert registration.status_code == 200
    deleted = await client.delete(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert deleted.status_code == 200
    assert (await client.get(f"{BASE}/{event['id']}")).status_code == 404
    registrations = (await db_session.execute(select(EventRegistration))).scalars().all()
    assert len(registrations) == 1
    assert registrations[0].student_id == student_user.id
    assert (
        await client.delete(f"{BASE}/{event['id']}", headers=auth_header(student_token))
    ).status_code == 403
    assert (await client.delete(f"{BASE}/{event['id']}")).status_code == 401


@pytest.mark.asyncio
async def test_register_confirms_then_waitlists_when_full(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    event = await create_event(client, admin_token, max_participants=1)
    first = await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    second = await client.post(
        f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token)
    )
    assert first.status_code == 200
    assert first.json()["data"]["status"] == "CONFIRMED"
    assert second.status_code == 200
    assert second.json()["data"]["status"] == "WAITLISTED"
    assert (await client.post(f"{BASE}/{event['id']}/register")).status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration_returns_conflict(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token)
    headers = auth_header(student_token)
    assert (await client.post(f"{BASE}/{event['id']}/register", headers=headers)).status_code == 200
    duplicate = await client.post(f"{BASE}/{event['id']}/register", headers=headers)
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_participants_are_admin_only(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    response = await client.get(f"{BASE}/{event['id']}/participants", headers=auth_header(admin_token))
    assert response.status_code == 200
    assert response.json()["data"][0]["student_email"] == "ada@unilag.edu.ng"
    assert (
        await client.get(f"{BASE}/{event['id']}/participants", headers=auth_header(student_token))
    ).status_code == 403
    assert (await client.get(f"{BASE}/{event['id']}/participants")).status_code == 401
