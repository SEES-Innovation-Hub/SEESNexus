from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.events import Event, EventRegistration, EventType
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


# --- virtual_link visibility (Tech Doc §5.5 keeps these routes public) ---


def virtual_event_payload(**overrides) -> dict:
    return event_payload(
        is_virtual=True, virtual_link="https://meet.example.com/secret-room", **overrides
    )


@pytest.mark.asyncio
async def test_virtual_link_is_hidden_from_anonymous_callers(
    client: AsyncClient, admin_token: str
):
    created = await client.post(
        BASE, json=virtual_event_payload(), headers=auth_header(admin_token)
    )
    assert created.status_code == 201
    event_id = created.json()["data"]["id"]

    detail = await client.get(f"{BASE}/{event_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["virtual_link"] is None

    listing = await client.get(BASE)
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
    detail = await client.get(f"{BASE}/{event['id']}")
    assert detail.json()["data"]["confirmed_count"] == 1
    assert detail.json()["data"]["spots_left"] == 0

    # A waitlisted signup holds no place, so neither number moves.
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token))
    listing = await client.get(BASE)
    item = listing.json()["data"]["items"][0]
    assert item["confirmed_count"] == 1
    assert item["spots_left"] == 0


@pytest.mark.asyncio
async def test_spots_left_is_null_when_participants_are_unlimited(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token, max_participants=None)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    detail = await client.get(f"{BASE}/{event['id']}")
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

    unfiltered = await client.get(BASE)
    assert unfiltered.json()["data"]["total"] == 2

    upcoming = await client.get(f"{BASE}?upcoming=true")
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
    detail = await client.get(f"{BASE}/{event['id']}")
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

    detail = await client.get(f"{BASE}/{event['id']}")
    assert detail.json()["data"]["end_date"] == original_end


# --- GET /events/registrations/my ---


@pytest.mark.asyncio
async def test_my_registrations_returns_only_the_callers_own(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    event = await create_event(client, admin_token)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token))

    mine = await client.get(f"{BASE}/registrations/my", headers=auth_header(student_token))
    assert mine.status_code == 200
    rows = mine.json()["data"]
    assert len(rows) == 1
    assert rows[0]["event_id"] == event["id"]
    assert rows[0]["event_title"] == event["title"]
    assert rows[0]["status"] == "CONFIRMED"

    assert (await client.get(f"{BASE}/registrations/my")).status_code == 401


@pytest.mark.asyncio
async def test_my_registrations_still_work_after_the_deadline(
    client: AsyncClient,
    db_session,
    admin_token: str,
    student_token: str,
    other_student_token: str,
    student_user: User,
):
    """The whole point of gap 1: closed sign-ups must not hide your own place."""
    event = await create_event(client, admin_token)
    registered = await client.post(
        f"{BASE}/{event['id']}/register", headers=auth_header(student_token)
    )
    assert registered.status_code == 200

    # Move the deadline and the start date into the past. Going through the API
    # is impossible: EventCreate and EventUpdate both reject past dates.
    now = datetime.now(timezone.utc)
    stored = (await db_session.execute(select(Event).where(Event.id == event["id"]))).scalar_one()
    stored.registration_deadline = now - timedelta(days=2)
    stored.start_date = now - timedelta(days=1)
    stored.end_date = now - timedelta(hours=20)
    await db_session.commit()

    mine = await client.get(f"{BASE}/registrations/my", headers=auth_header(student_token))
    assert mine.status_code == 200
    assert len(mine.json()["data"]) == 1
    assert mine.json()["data"][0]["student_id"] == student_user.id

    # Registering afresh is still closed, which is the behaviour being preserved:
    # the deadline blocks new sign-ups, it does not hide existing ones.
    late = await client.post(
        f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token)
    )
    assert late.status_code == 400
    assert late.json()["message"] == "Registration deadline has passed"


@pytest.mark.asyncio
async def test_my_registrations_hides_the_link_unless_confirmed(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    created = await client.post(
        BASE, json=virtual_event_payload(max_participants=1), headers=auth_header(admin_token)
    )
    event_id = created.json()["data"]["id"]
    await client.post(f"{BASE}/{event_id}/register", headers=auth_header(student_token))
    await client.post(f"{BASE}/{event_id}/register", headers=auth_header(other_student_token))

    confirmed = await client.get(f"{BASE}/registrations/my", headers=auth_header(student_token))
    assert confirmed.json()["data"][0]["virtual_link"] == "https://meet.example.com/secret-room"

    waitlisted = await client.get(
        f"{BASE}/registrations/my", headers=auth_header(other_student_token)
    )
    assert waitlisted.json()["data"][0]["status"] == "WAITLISTED"
    assert waitlisted.json()["data"][0]["virtual_link"] is None


# --- DELETE /events/{id}/register ---


@pytest.mark.asyncio
async def test_cancelling_a_confirmed_place_promotes_the_first_waitlisted_student(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str,
    other_student_user: User,
):
    event = await create_event(client, admin_token, max_participants=1)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    waitlisted = await client.post(
        f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token)
    )
    assert waitlisted.json()["data"]["status"] == "WAITLISTED"

    cancelled = await client.delete(
        f"{BASE}/{event['id']}/register", headers=auth_header(student_token)
    )
    assert cancelled.status_code == 200
    body = cancelled.json()["data"]
    assert body["registration"]["status"] == "CANCELLED"
    assert body["promoted_student_id"] == other_student_user.id

    promoted = await client.get(
        f"{BASE}/registrations/my", headers=auth_header(other_student_token)
    )
    assert promoted.json()["data"][0]["status"] == "CONFIRMED"

    # The freed place is accounted for, not double-counted.
    detail = await client.get(f"{BASE}/{event['id']}")
    assert detail.json()["data"]["confirmed_count"] == 1
    assert detail.json()["data"]["spots_left"] == 0


@pytest.mark.asyncio
async def test_cancelling_a_waitlisted_place_promotes_nobody(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    event = await create_event(client, admin_token, max_participants=1)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token))

    cancelled = await client.delete(
        f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token)
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["promoted_student_id"] is None

    # The confirmed student is untouched.
    detail = await client.get(f"{BASE}/{event['id']}")
    assert detail.json()["data"]["confirmed_count"] == 1


@pytest.mark.asyncio
async def test_cancel_rejects_second_attempt_and_unregistered_callers(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    event = await create_event(client, admin_token)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))

    first = await client.delete(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    assert first.status_code == 200

    again = await client.delete(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    assert again.status_code == 409

    never = await client.delete(
        f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token)
    )
    assert never.status_code == 404

    assert (await client.delete(f"{BASE}/{event['id']}/register")).status_code == 401


@pytest.mark.asyncio
async def test_a_cancelled_student_can_register_again(
    client: AsyncClient, admin_token: str, student_token: str
):
    """The unique constraint would otherwise lock a student out permanently."""
    event = await create_event(client, admin_token, max_participants=1)
    headers = auth_header(student_token)
    await client.post(f"{BASE}/{event['id']}/register", headers=headers)
    await client.delete(f"{BASE}/{event['id']}/register", headers=headers)

    again = await client.post(f"{BASE}/{event['id']}/register", headers=headers)
    assert again.status_code == 200
    assert again.json()["data"]["status"] == "CONFIRMED"

    # Still one row, not two -- the cancelled row was revived.
    mine = await client.get(f"{BASE}/registrations/my", headers=headers)
    assert len(mine.json()["data"]) == 1


@pytest.mark.asyncio
async def test_rejoining_a_full_event_lands_on_the_waitlist(
    client: AsyncClient, admin_token: str, student_token: str, other_student_token: str
):
    event = await create_event(client, admin_token, max_participants=1)
    mine = auth_header(student_token)
    await client.post(f"{BASE}/{event['id']}/register", headers=mine)

    # Cancelling promotes the other student into the only place.
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(other_student_token))
    await client.delete(f"{BASE}/{event['id']}/register", headers=mine)

    rejoined = await client.post(f"{BASE}/{event['id']}/register", headers=mine)
    assert rejoined.status_code == 200
    assert rejoined.json()["data"]["status"] == "WAITLISTED"


# --- POST /events/{id}/restore ---


@pytest.mark.asyncio
async def test_restore_brings_a_deleted_event_back(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token)
    await client.post(f"{BASE}/{event['id']}/register", headers=auth_header(student_token))
    await client.delete(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert (await client.get(f"{BASE}/{event['id']}")).status_code == 404

    restored = await client.post(
        f"{BASE}/{event['id']}/restore", headers=auth_header(admin_token)
    )
    assert restored.status_code == 200
    assert restored.json()["data"]["id"] == event["id"]

    assert (await client.get(f"{BASE}/{event['id']}")).status_code == 200
    # Registrations survive a soft delete, so they come back with the event.
    assert (await client.get(f"{BASE}/{event['id']}")).json()["data"]["confirmed_count"] == 1


@pytest.mark.asyncio
async def test_restore_rejects_a_live_event_and_non_admins(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token)

    live = await client.post(f"{BASE}/{event['id']}/restore", headers=auth_header(admin_token))
    assert live.status_code == 400
    assert live.json()["message"] == "Event is not deleted"

    await client.delete(f"{BASE}/{event['id']}", headers=auth_header(admin_token))
    assert (
        await client.post(f"{BASE}/{event['id']}/restore", headers=auth_header(student_token))
    ).status_code == 403
    assert (await client.post(f"{BASE}/{event['id']}/restore")).status_code == 401


@pytest.mark.asyncio
async def test_include_deleted_is_admin_only(
    client: AsyncClient, admin_token: str, student_token: str
):
    event = await create_event(client, admin_token)
    await client.delete(f"{BASE}/{event['id']}", headers=auth_header(admin_token))

    hidden = await client.get(BASE)
    assert hidden.json()["data"]["total"] == 0

    found = await client.get(f"{BASE}?include_deleted=true", headers=auth_header(admin_token))
    assert found.status_code == 200
    assert [item["id"] for item in found.json()["data"]["items"]] == [event["id"]]

    # 403 for a logged-in non-admin, 401 with no token, as everywhere else.
    assert (
        await client.get(f"{BASE}?include_deleted=true", headers=auth_header(student_token))
    ).status_code == 403
    assert (await client.get(f"{BASE}?include_deleted=true")).status_code == 401


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
