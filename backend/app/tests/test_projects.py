from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.project import Project, ProjectCategory, ProjectMember, ProjectStatus
from app.models.user import User, UserRole
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/projects"
SEED_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)


def payload(**overrides) -> dict:
    body = {
        "title": "Smart Meter",
        "description": "A prepaid energy meter with remote reads.",
        "tech_stack": ["Python", "ESP32"],
        "category": "IOT",
    }
    body.update(overrides)
    return body


async def seed_project(db: AsyncSession, creator: User, *, offset: int = 0, **overrides) -> Project:
    """Insert a project directly, with an explicit created_at so ordering is deterministic."""
    fields = {
        "title": f"Project {offset}",
        "description": "Seeded.",
        "tech_stack": ["Python"],
        "category": ProjectCategory.IOT,
        "status": ProjectStatus.IDEATION,
        "created_by_id": creator.id,
        "created_at": SEED_EPOCH + timedelta(minutes=offset),
    }
    fields.update(overrides)
    project = Project(**fields)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@pytest_asyncio.fixture
async def other_student_user(db_session: AsyncSession) -> User:
    """A second non-admin, for the not-the-creator permission paths."""
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
        "/api/v1/auth/login", json={"email": other_student_user.email, "password": "StrongPass2"}
    )
    return resp.json()["data"]["access_token"]


# --- GET /projects (public) ---


async def test_list_is_public(client: AsyncClient, db_session: AsyncSession, student_user: User):
    await seed_project(db_session, student_user)

    resp = await client.get(BASE)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["total"] == 1
    assert len(body["data"]["items"]) == 1


async def test_list_orders_by_created_at_desc(
    client: AsyncClient, db_session: AsyncSession, student_user: User
):
    for i in range(3):
        await seed_project(db_session, student_user, offset=i, title=f"P{i}")

    resp = await client.get(BASE)
    titles = [item["title"] for item in resp.json()["data"]["items"]]
    assert titles == ["P2", "P1", "P0"]


async def test_detail_is_public(client: AsyncClient, db_session: AsyncSession, student_user: User):
    project = await seed_project(db_session, student_user)

    resp = await client.get(f"{BASE}/{project.id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == project.id


async def test_detail_unknown_id_404(client: AsyncClient):
    resp = await client.get(f"{BASE}/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["status"] == "error"


# --- POST /projects ---


async def test_create_as_plain_student(client: AsyncClient, student_token: str, student_user: User):
    resp = await client.post(BASE, json=payload(), headers=auth_header(student_token))
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["title"] == "Smart Meter"
    assert data["status"] == "IDEATION"
    assert data["created_by_id"] == student_user.id


async def test_create_requires_auth(client: AsyncClient):
    resp = await client.post(BASE, json=payload())
    assert resp.status_code == 401


async def test_create_ignores_created_by_in_body(
    client: AsyncClient, student_token: str, student_user: User, admin_user: User
):
    resp = await client.post(
        BASE, json=payload(created_by_id=admin_user.id), headers=auth_header(student_token)
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["created_by_id"] == student_user.id


async def test_create_with_members(
    client: AsyncClient, student_token: str, student_user: User, admin_user: User
):
    resp = await client.post(
        BASE,
        json=payload(member_ids=[student_user.id, admin_user.id]),
        headers=auth_header(student_token),
    )
    assert resp.status_code == 201
    member_ids = {m["id"] for m in resp.json()["data"]["members"]}
    assert member_ids == {student_user.id, admin_user.id}


async def test_create_unknown_member_id_400(client: AsyncClient, student_token: str):
    resp = await client.post(
        BASE, json=payload(member_ids=["ghost"]), headers=auth_header(student_token)
    )
    assert resp.status_code == 400
    assert resp.json()["status"] == "error"


# --- PUT /projects/{id} ---


async def test_update_by_creator(
    client: AsyncClient, db_session: AsyncSession, student_user: User, student_token: str
):
    project = await seed_project(db_session, student_user)

    resp = await client.put(
        f"{BASE}/{project.id}", json={"title": "Renamed"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "Renamed"
    # exclude_unset: untouched fields survive
    assert data["description"] == "Seeded."


async def test_update_by_admin_who_is_not_creator(
    client: AsyncClient, db_session: AsyncSession, student_user: User, admin_token: str
):
    project = await seed_project(db_session, student_user)

    resp = await client.put(
        f"{BASE}/{project.id}", json={"status": "COMPLETED"}, headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "COMPLETED"


async def test_update_by_unrelated_student_403(
    client: AsyncClient, db_session: AsyncSession, student_user: User, other_student_token: str
):
    project = await seed_project(db_session, student_user)

    resp = await client.put(
        f"{BASE}/{project.id}", json={"title": "Hijacked"}, headers=auth_header(other_student_token)
    )
    assert resp.status_code == 403


async def test_update_unknown_id_404_not_403(client: AsyncClient, other_student_token: str):
    resp = await client.put(
        f"{BASE}/does-not-exist", json={"title": "X"}, headers=auth_header(other_student_token)
    )
    assert resp.status_code == 404


async def test_update_replaces_members_rather_than_appending(
    client: AsyncClient, student_token: str, student_user: User, admin_user: User
):
    created = await client.post(
        BASE, json=payload(member_ids=[student_user.id]), headers=auth_header(student_token)
    )
    project_id = created.json()["data"]["id"]

    resp = await client.put(
        f"{BASE}/{project_id}",
        json={"member_ids": [admin_user.id]},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 200
    member_ids = [m["id"] for m in resp.json()["data"]["members"]]
    assert member_ids == [admin_user.id]


async def test_update_unknown_member_id_400(
    client: AsyncClient, db_session: AsyncSession, student_user: User, student_token: str
):
    project = await seed_project(db_session, student_user)

    resp = await client.put(
        f"{BASE}/{project.id}", json={"member_ids": ["ghost"]}, headers=auth_header(student_token)
    )
    assert resp.status_code == 400


# --- DELETE /projects/{id} ---


async def test_delete_by_creator_returns_envelope(
    client: AsyncClient, db_session: AsyncSession, student_user: User, student_token: str
):
    project = await seed_project(db_session, student_user)

    resp = await client.delete(f"{BASE}/{project.id}", headers=auth_header(student_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    remaining = await db_session.execute(select(func.count()).select_from(Project))
    assert remaining.scalar_one() == 0


async def test_delete_by_unrelated_student_403(
    client: AsyncClient, db_session: AsyncSession, student_user: User, other_student_token: str
):
    project = await seed_project(db_session, student_user)

    resp = await client.delete(f"{BASE}/{project.id}", headers=auth_header(other_student_token))
    assert resp.status_code == 403


async def test_delete_unknown_id_404(client: AsyncClient, admin_token: str):
    resp = await client.delete(f"{BASE}/does-not-exist", headers=auth_header(admin_token))
    assert resp.status_code == 404


async def test_delete_removes_member_rows(
    client: AsyncClient,
    db_session: AsyncSession,
    student_token: str,
    student_user: User,
    admin_user: User,
):
    created = await client.post(
        BASE,
        json=payload(member_ids=[student_user.id, admin_user.id]),
        headers=auth_header(student_token),
    )
    project_id = created.json()["data"]["id"]

    before = await db_session.execute(select(func.count()).select_from(ProjectMember))
    assert before.scalar_one() == 2

    resp = await client.delete(f"{BASE}/{project_id}", headers=auth_header(student_token))
    assert resp.status_code == 200

    after = await db_session.execute(select(func.count()).select_from(ProjectMember))
    assert after.scalar_one() == 0


# --- filtering ---


async def test_filter_by_category(client: AsyncClient, db_session: AsyncSession, student_user: User):
    await seed_project(db_session, student_user, offset=0, category=ProjectCategory.IOT)
    await seed_project(db_session, student_user, offset=1, category=ProjectCategory.WEB)

    resp = await client.get(BASE, params={"category": "IOT"})
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["category"] == "IOT"


async def test_filter_by_status(client: AsyncClient, db_session: AsyncSession, student_user: User):
    await seed_project(db_session, student_user, offset=0, status=ProjectStatus.COMPLETED)
    await seed_project(db_session, student_user, offset=1, status=ProjectStatus.IDEATION)

    resp = await client.get(BASE, params={"status": "COMPLETED"})
    items = resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["status"] == "COMPLETED"


async def test_filter_by_category_and_status(
    client: AsyncClient, db_session: AsyncSession, student_user: User
):
    await seed_project(
        db_session,
        student_user,
        offset=0,
        category=ProjectCategory.IOT,
        status=ProjectStatus.COMPLETED,
    )
    await seed_project(
        db_session,
        student_user,
        offset=1,
        category=ProjectCategory.IOT,
        status=ProjectStatus.IDEATION,
    )
    await seed_project(
        db_session,
        student_user,
        offset=2,
        category=ProjectCategory.WEB,
        status=ProjectStatus.COMPLETED,
    )

    resp = await client.get(BASE, params={"category": "IOT", "status": "COMPLETED"})
    data = resp.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Project 0"


# --- pagination ---


async def test_pagination_second_page_slice(
    client: AsyncClient, db_session: AsyncSession, student_user: User
):
    for i in range(25):
        await seed_project(db_session, student_user, offset=i, title=f"P{i:02d}")

    resp = await client.get(BASE, params={"page": 2, "page_size": 10})
    data = resp.json()["data"]
    assert data["total"] == 25
    assert data["total_pages"] == 3
    assert data["page"] == 2
    # Newest first: page 1 is P24..P15, so page 2 is P14..P05.
    assert [item["title"] for item in data["items"]] == [f"P{i:02d}" for i in range(14, 4, -1)]


async def test_page_size_clamped_to_100(
    client: AsyncClient, db_session: AsyncSession, student_user: User
):
    for i in range(3):
        await seed_project(db_session, student_user, offset=i)

    resp = await client.get(BASE, params={"page_size": 1000})
    assert resp.status_code == 200
    assert resp.json()["data"]["page_size"] == 100


# --- tech_stack validation ---


async def test_tech_stack_round_trips_as_list(client: AsyncClient, student_token: str):
    resp = await client.post(
        BASE,
        json=payload(tech_stack=["Python", "ESP32", "MQTT"]),
        headers=auth_header(student_token),
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["tech_stack"] == ["Python", "ESP32", "MQTT"]


async def test_tech_stack_strips_blanks_and_deduplicates(client: AsyncClient, student_token: str):
    resp = await client.post(
        BASE,
        json=payload(tech_stack=["  Python  ", "Python", "", "   ", "FastAPI"]),
        headers=auth_header(student_token),
    )
    assert resp.status_code == 201
    assert resp.json()["data"]["tech_stack"] == ["Python", "FastAPI"]


async def test_tech_stack_rejects_oversized_entry(client: AsyncClient, student_token: str):
    resp = await client.post(
        BASE, json=payload(tech_stack=["x" * 51]), headers=auth_header(student_token)
    )
    assert resp.status_code == 422


async def test_tech_stack_rejects_too_many_entries(client: AsyncClient, student_token: str):
    resp = await client.post(
        BASE,
        json=payload(tech_stack=[f"lib{i}" for i in range(21)]),
        headers=auth_header(student_token),
    )
    assert resp.status_code == 422


async def test_tech_stack_validated_on_update(
    client: AsyncClient, db_session: AsyncSession, student_user: User, student_token: str
):
    project = await seed_project(db_session, student_user)

    resp = await client.put(
        f"{BASE}/{project.id}",
        json={"tech_stack": [" Django ", "Django"]},
        headers=auth_header(student_token),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["tech_stack"] == ["Django"]


# --- privacy ---


async def test_no_member_email_in_responses(
    client: AsyncClient, student_token: str, student_user: User, admin_user: User
):
    created = await client.post(
        BASE,
        json=payload(member_ids=[student_user.id, admin_user.id]),
        headers=auth_header(student_token),
    )
    project_id = created.json()["data"]["id"]

    for resp in (
        created,
        await client.get(BASE),
        await client.get(f"{BASE}/{project_id}"),
    ):
        assert student_user.email not in resp.text
        assert admin_user.email not in resp.text
        assert "email" not in resp.text
