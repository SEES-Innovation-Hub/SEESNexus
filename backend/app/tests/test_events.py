from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import hash_password
from app.models.events import Event, EventRegistration, EventType
from app.models.user import User, UserRole
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
async def test_list_events_requires_login_and_is_paginated(
    client: AsyncClient, admin_token: str, student_token: str
):
    await create_event(client, admin_token)
    assert (await client.get(BASE)).status_code == 401
    response = await client.get(f"{BASE}?page=1&page_size=10", headers=auth_header(student_token))
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["data"]["total"] == 1


@pytest.mark.asyncio
async def test_get_event_requires_login(client: AsyncClient, admin_token: str, student_token: str):
    event = await create_event(client, admin_token)
    assert (await client.get(f"{BASE}/{event['id']}")).status_code == 401
    response = await client.get(f"{BASE}/{event['id']}", headers=auth_header(student_token))
    assert response.status_code == 200
    assert response.json()["data"]["id"] == event["id"]


@pytest.mark.asyncio
async def test_get_unknown_event_returns_enveloped_404(client: AsyncClient, student_token: str):
    response = await client.get(f"{BASE}/missing-event", headers=auth_header(student_token))
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
    assert (
        await client.get(f"{BASE}/{event['id']}", headers=auth_header(student_token))
    ).status_code == 404
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


# --- virtual_link visibility ---


def virtual_event_payload(**overrides) -> dict:
    return event_payload(
        is_virtual=True, virtual_link="https://meet.example.com/secret-room", **overrides
    )


@pytest.mark.asyncio
async def test_event_reads_are_closed_to_anonymous_callers(
    client: AsyncClient, admin_token: str, student_token: str
):
    created = await client.post(
        BASE, json=virtual_event_payload(), headers=auth_header(admin_token)
    )
    assert created.status_code == 201
    event_id = created.json()["data"]["id"]

    # No login, no event -- and so no link either.
    assert (await client.get(f"{BASE}/{event_id}")).status_code == 401
    assert (await client.get(BASE)).status_code == 401

    # A member who has not registered sees the event but not the link.
    listing = await client.get(BASE, headers=auth_header(student_token))
    assert listing.json()["data"]["items"][0]["virtual_link"] is None


@pytest.mark.asyncio
async def test_virtual_link_goes_to_confirmed_students_and_admins_only(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    created = await client.post(
        BASE, json=virtual_event_payload(max_participants=1), headers=auth_header(admin_token)
    )
    event_id = created.json()["data"]["id"]
    link = "https://meet.example.com/secret-room"

    # The admin runs the event.
    admin_view = await client.get(f"{BASE}/{event_id}", headers=auth_header(admin_token))
    assert admin_view.json()["data"]["virtual_link"] == link

    # A student with no registration gets nothing.
    stranger = await client.get(f"{BASE}/{event_id}", headers=auth_header(student_token))
    assert stranger.json()["data"]["virtual_link"] is None

    # Confirmed: the link appears.
    await client.post(f"{BASE}/{event_id}/register", headers=auth_header(student_token))
    confirmed = await client.get(f"{BASE}/{event_id}", headers=auth_header(student_token))
    assert confirmed.json()["data"]["virtual_link"] == link

    # Waitlisted: still nothing, because no place is held yet.
    waitlisted = await client.post(
        f"{BASE}/{event_id}/register", headers=auth_header(other_student_token)
    )
    assert waitlisted.json()["data"]["status"] == "WAITLISTED"
    held_back = await client.get(f"{BASE}/{event_id}", headers=auth_header(other_student_token))
    assert held_back.json()["data"]["virtual_link"] is None


@pytest.mark.asyncio
async def test_event_reads_reject_a_bad_token_rather_than_degrading(
    client: AsyncClient, admin_token: str
):
    """A broken token is an error, not an anonymous caller.

    Treating an expired token as anonymous would silently hide the meeting link
    from a confirmed student instead of prompting a token refresh.
    """
    await create_event(client, admin_token)
    assert (await client.get(BASE, headers=auth_header("garbage.token.here"))).status_code == 401
    assert (
        await client.get(f"{BASE}/missing", headers=auth_header("garbage.token.here"))
    ).status_code == 401


# --- confirmed_count / spots_left ---


@pytest.mark.asyncio
async def test_confirmed_count_and_spots_left(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    event = await create_event(client, admin_token, max_participants=1)
    assert event["confirmed_count"] == 0
    assert event["spots_left"] == 1

    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    detail = await client.get(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert detail.json()["data"]["confirmed_count"] == 1
    assert detail.json()["data"]["spots_left"] == 0

    # A waitlisted signup holds no place, so neither number moves.
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token))
    listing = await client.get(BASE, headers=auth_header(admin_token))
    item = listing.json()["data"]["items"][0]
    assert item["confirmed_count"] == 1
    assert item["spots_left"] == 0


@pytest.mark.asyncio
async def test_spots_left_is_null_when_participants_are_unlimited(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token, max_participants=None)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    detail = await client.get(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert detail.json()["data"]["confirmed_count"] == 1
    assert detail.json()["data"]["spots_left"] is None


# --- upcoming filter ---


@pytest.mark.asyncio
async def test_upcoming_filter_excludes_events_that_already_started(
    client: AsyncClient, db_session, admin_token: str, admin_user: User
):
    future = await create_event(client, admin_token, title="Future Event")

    # Inserted directly: EventCreate rejects past dates, so a started event
    # cannot be made through the API.
    now = datetime.now(timezone.utc)
    past = Event(
        title="Past Event",
        description="Already happened.",
        event_type=EventType.WORKSHOP,
        location="Lab 2",
        is_virtual=False,
        start_date=now - timedelta(days=2),
        end_date=now - timedelta(days=1),
        registration_deadline=now - timedelta(days=3),
        created_by_id=admin_user.id,
    )
    db_session.add(past)
    await db_session.commit()

    unfiltered = await client.get(BASE, headers=auth_header(admin_token))
    assert unfiltered.json()["data"]["total"] == 2

    upcoming = await client.get(f"{BASE}?upcoming=true", headers=auth_header(admin_token))
    titles = [item["title"] for item in upcoming.json()["data"]["items"]]
    assert titles == ["Future Event"]
    assert upcoming.json()["data"]["total"] == 1
    assert future["title"] == "Future Event"


# --- max_participants floor ---


@pytest.mark.asyncio
async def test_max_participants_cannot_drop_below_confirmed_count(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    event = await create_event(client, admin_token, max_participants=2)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token))

    rejected = await client.put(
        f"{BASE}/{event['id']}", json={"max_participants": 1}, headers=auth_header(admin_token)
    )
    assert rejected.status_code == 400
    body = rejected.json()
    assert body["status"] == "error"
    assert "confirmed registrations" in body["message"]

    # The stored value is untouched by the rejected update.
    detail = await client.get(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert detail.json()["data"]["max_participants"] == 2

    # Raising it, or holding it at the confirmed count, is allowed.
    assert (
        await client.put(
            f"{BASE}/{event['id']}",
            json={"max_participants": 2},
            headers=auth_header(admin_token),
        )
    ).status_code == 200
    assert (
        await client.put(
            f"{BASE}/{event['id']}",
            json={"max_participants": 5},
            headers=auth_header(admin_token),
        )
    ).status_code == 200


@pytest.mark.asyncio
async def test_rejected_date_update_does_not_persist(
    client: AsyncClient, admin_token: str
):
    """A 400 must not leave the rejected values on the row.

    The fields are assigned before the dates are validated, so without an
    explicit rollback the next query in the session flushes them.
    """
    event = await create_event(client, admin_token)
    original_end = event["end_date"]

    rejected = await client.put(
        f"{BASE}/{event['id']}",
        json={"end_date": event["start_date"]},
        headers=auth_header(admin_token),
    )
    assert rejected.status_code == 400
    assert rejected.json()["status"] == "error"

    detail = await client.get(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert detail.json()["data"]["end_date"] == original_end


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


# --- shared helpers for the registration lifecycle ---


@pytest_asyncio.fixture
async def third_student_token(client: AsyncClient, db_session) -> str:
    user = User(
        full_name="Tolu Student",
        email="tolu@unilag.edu.ng",
        password=hash_password("StrongPass3"),
        department="EEE",
        level="100 Level",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    await db_session.commit()
    resp = await client.post(
        "/api/v1/auth/login", json={"email": user.email, "password": "StrongPass3"}
    )
    return resp.json()["data"]["access_token"]


async def register(client: AsyncClient, event_id: str, token: str) -> dict:
    response = await client.post(f"{BASE}/{event_id}/register", headers=auth_header(token))
    assert response.status_code == 200, response.text
    return response.json()["data"]


async def my_registrations(client: AsyncClient, token: str) -> list[dict]:
    response = await client.get(f"{BASE}/registrations/my", headers=auth_header(token))
    assert response.status_code == 200, response.text
    return response.json()["data"]


# --- GET /events/registrations/my ---


@pytest.mark.asyncio
async def test_my_registrations_lists_only_the_callers_own(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    mine = await create_event(client, admin_token, title="Mine", max_participants=5)
    theirs = await create_event(client, admin_token, title="Theirs")
    await register(client, mine["id"], student_token)
    await register(client, theirs["id"], other_student_token)

    rows = await my_registrations(client, student_token)
    assert [row["event"]["title"] for row in rows] == ["Mine"]
    row = rows[0]
    assert row["status"] == "CONFIRMED"
    assert row["event_id"] == mine["id"]
    assert row["event_deleted"] is False
    assert row["waitlist_position"] is None
    assert row["event"]["confirmed_count"] == 1

    assert (await client.get(f"{BASE}/registrations/my")).status_code == 401


@pytest.mark.asyncio
async def test_my_registrations_survive_the_deadline_and_show_deleted_events(
    client: AsyncClient, db_session, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token)
    await register(client, event["id"], student_token)

    # Move the deadline (and the event) into the past, as time would.
    row = (await db_session.execute(select(Event).where(Event.id == event["id"]))).scalar_one()
    now = datetime.now(timezone.utc)
    row.registration_deadline = now - timedelta(days=2)
    row.start_date = now - timedelta(days=1)
    row.end_date = now - timedelta(hours=1)
    await db_session.commit()

    rows = await my_registrations(client, student_token)
    assert len(rows) == 1 and rows[0]["status"] == "CONFIRMED"

    await client.delete(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    rows = await my_registrations(client, student_token)
    assert rows[0]["event_deleted"] is True


@pytest.mark.asyncio
async def test_my_registrations_gives_waitlist_position_and_link_rules(
    client: AsyncClient,
    admin_token: str,
    student_token: str,
    other_student_token: str,
    third_student_token: str,
):
    created = await client.post(
        BASE, json=virtual_event_payload(max_participants=1), headers=auth_header(admin_token)
    )
    event_id = created.json()["data"]["id"]
    await register(client, event_id, student_token)
    await register(client, event_id, other_student_token)
    await register(client, event_id, third_student_token)

    confirmed = (await my_registrations(client, student_token))[0]
    assert confirmed["event"]["virtual_link"] == "https://meet.example.com/secret-room"

    second = (await my_registrations(client, other_student_token))[0]
    third = (await my_registrations(client, third_student_token))[0]
    assert (second["status"], second["waitlist_position"]) == ("WAITLISTED", 1)
    assert (third["status"], third["waitlist_position"]) == ("WAITLISTED", 2)
    assert second["event"]["virtual_link"] is None


# --- DELETE /events/{id}/register ---


@pytest.mark.asyncio
async def test_cancelling_a_confirmed_place_promotes_the_first_waitlisted(
    client: AsyncClient,
    admin_token: str,
    student_token: str,
    other_student_token: str,
    third_student_token: str,
):
    event = await create_event(client, admin_token, max_participants=1)
    await register(client, event["id"], student_token)
    await register(client, event["id"], other_student_token)
    await register(client, event["id"], third_student_token)

    cancelled = await client.delete(
        f"{BASE}/{event['id']}/register", headers=auth_header(student_token)
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "CANCELLED"

    # First in the queue moves up; the second stays waiting, now at the front.
    promoted = (await my_registrations(client, other_student_token))[0]
    assert promoted["status"] == "CONFIRMED"
    still_waiting = (await my_registrations(client, third_student_token))[0]
    assert (still_waiting["status"], still_waiting["waitlist_position"]) == ("WAITLISTED", 1)

    detail = await client.get(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert detail.json()["data"]["confirmed_count"] == 1
    assert detail.json()["data"]["spots_left"] == 0


@pytest.mark.asyncio
async def test_cancelling_a_waitlisted_place_promotes_nobody(
    client: AsyncClient,
    admin_token: str,
    student_token: str,
    other_student_token: str,
    third_student_token: str,
):
    event = await create_event(client, admin_token, max_participants=1)
    await register(client, event["id"], student_token)
    await register(client, event["id"], other_student_token)
    await register(client, event["id"], third_student_token)

    response = await client.delete(
        f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token)
    )
    assert response.status_code == 200

    assert (await my_registrations(client, student_token))[0]["status"] == "CONFIRMED"
    third = (await my_registrations(client, third_student_token))[0]
    assert (third["status"], third["waitlist_position"]) == ("WAITLISTED", 1)


@pytest.mark.asyncio
async def test_cancel_then_register_again_rejoins_the_back_of_the_queue(
    client: AsyncClient,
    admin_token: str,
    student_token: str,
    other_student_token: str,
    third_student_token: str,
):
    event = await create_event(client, admin_token, max_participants=1)
    await register(client, event["id"], student_token)
    await register(client, event["id"], other_student_token)
    await register(client, event["id"], third_student_token)

    await client.delete(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    # Cancelling twice is a 404: there is no live registration left to cancel.
    again = await client.delete(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    assert again.status_code == 404

    back = await register(client, event["id"], student_token)
    assert back["status"] == "WAITLISTED"
    rows = await my_registrations(client, student_token)
    assert rows[0]["waitlist_position"] == 2


@pytest.mark.asyncio
async def test_cancel_rules(
    client: AsyncClient, db_session, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token)

    # Never registered.
    missing = await client.delete(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    assert missing.status_code == 404
    assert (await client.delete(f"{BASE}/{event['id']}/register")).status_code == 401

    # Allowed after the deadline -- that is when a freed place matters most.
    await register(client, event["id"], student_token)
    row = (await db_session.execute(select(Event).where(Event.id == event["id"]))).scalar_one()
    row.registration_deadline = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()
    ok = await client.delete(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    assert ok.status_code == 200

    # But not once the event has started.
    other = await create_event(client, admin_token, title="Started")
    await register(client, other["id"], student_token)
    row = (await db_session.execute(select(Event).where(Event.id == other["id"]))).scalar_one()
    now = datetime.now(timezone.utc)
    row.registration_deadline = now - timedelta(hours=2)
    row.start_date = now - timedelta(hours=1)
    await db_session.commit()
    late = await client.delete(f"{BASE}/{other['id']}/register", headers=auth_header(student_token))
    assert late.status_code == 400
    assert "already started" in late.json()["message"]


@pytest.mark.asyncio
async def test_raising_the_cap_promotes_waitlisted_students(
    client: AsyncClient,
    admin_token: str,
    student_token: str,
    other_student_token: str,
    third_student_token: str,
):
    event = await create_event(client, admin_token, max_participants=1)
    await register(client, event["id"], student_token)
    await register(client, event["id"], other_student_token)
    await register(client, event["id"], third_student_token)

    raised = await client.put(
        f"{BASE}/{event['id']}", json={"max_participants": 2}, headers=auth_header(admin_token)
    )
    assert raised.status_code == 200
    assert raised.json()["data"]["confirmed_count"] == 2
    assert (await my_registrations(client, other_student_token))[0]["status"] == "CONFIRMED"
    assert (await my_registrations(client, third_student_token))[0]["status"] == "WAITLISTED"

    # Removing the cap entirely lets everyone in.
    unlimited = await client.put(
        f"{BASE}/{event['id']}", json={"max_participants": None}, headers=auth_header(admin_token)
    )
    assert unlimited.json()["data"]["confirmed_count"] == 3
    assert unlimited.json()["data"]["spots_left"] is None


# --- restoring deleted events ---


@pytest.mark.asyncio
async def test_admin_can_list_and_restore_deleted_events(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token, title="Oops")
    await register(client, event["id"], student_token)
    await client.delete(f"{BASE}/{event['id']}", headers=auth_header(admin_token))

    # Students cannot see deleted events, by list or by id.
    assert (
        await client.get(f"{BASE}?deleted=true", headers=auth_header(student_token))
    ).status_code == 403
    assert (
        await client.get(f"{BASE}/{event['id']}", headers=auth_header(student_token))
    ).status_code == 404

    # Admins can, so they can find what to restore.
    deleted = await client.get(f"{BASE}?deleted=true", headers=auth_header(admin_token))
    items = deleted.json()["data"]["items"]
    assert [i["title"] for i in items] == ["Oops"]
    assert items[0]["deleted_at"] is not None
    live = await client.get(BASE, headers=auth_header(admin_token))
    assert live.json()["data"]["total"] == 0

    assert (
        await client.post(f"{BASE}/{event['id']}/restore", headers=auth_header(student_token))
    ).status_code == 403
    restored = await client.post(f"{BASE}/{event['id']}/restore", headers=auth_header(admin_token))
    assert restored.status_code == 200
    assert restored.json()["data"]["deleted_at"] is None
    # The registration came back with it.
    assert restored.json()["data"]["confirmed_count"] == 1

    again = await client.post(f"{BASE}/{event['id']}/restore", headers=auth_header(admin_token))
    assert again.status_code == 400
    assert (
        await client.post(f"{BASE}/missing/restore", headers=auth_header(admin_token))
    ).status_code == 404

    visible = await client.get(f"{BASE}/{event['id']}", headers=auth_header(student_token))
    assert visible.status_code == 200
