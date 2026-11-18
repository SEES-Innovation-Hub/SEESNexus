import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/users"


@pytest_asyncio.fixture
async def seeded_users(db_session: AsyncSession, student_user: User) -> list[User]:
    """Seed a handful of users with distinct full_names for search coverage."""
    extras = []
    for i, name in enumerate(["Chidi Okafor", "Amaka Nwosu", "Chinonso Okoli", "Zainab Bello"]):
        user = User(
            full_name=name,
            email=f"user{i}@unilag.edu.ng",
            password=hash_password("Pass1234"),
            department="EEE",
            level="200 Level",
            role=UserRole.STUDENT,
        )
        db_session.add(user)
        extras.append(user)
    await db_session.commit()
    for u in extras:
        await db_session.refresh(u)
    return extras


async def test_search_requires_auth(client: AsyncClient):
    resp = await client.get(f"{BASE}/search", params={"q": "ada"})
    assert resp.status_code == 401


async def test_search_substring_match_case_insensitive(
    client: AsyncClient, student_token: str, seeded_users: list[User]
):
    resp = await client.get(
        f"{BASE}/search", params={"q": "chi"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 200
    names = [row["full_name"] for row in resp.json()["data"]]
    # Chidi and Chinonso both contain "chi" (case-insensitive).
    assert "Chidi Okafor" in names
    assert "Chinonso Okoli" in names
    # Amaka does not.
    assert "Amaka Nwosu" not in names


async def test_search_returns_only_safe_fields(
    client: AsyncClient, student_token: str, seeded_users: list[User]
):
    resp = await client.get(
        f"{BASE}/search", params={"q": "amaka"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert len(rows) == 1
    row = rows[0]
    assert set(row.keys()) == {"id", "full_name", "profile_image_url"}


async def test_search_excludes_inactive_users(
    client: AsyncClient,
    db_session: AsyncSession,
    student_token: str,
    seeded_users: list[User],
):
    chidi = next(u for u in seeded_users if u.full_name == "Chidi Okafor")
    chidi.is_active = False
    await db_session.commit()

    resp = await client.get(
        f"{BASE}/search", params={"q": "chidi"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


async def test_search_caps_at_ten_results(
    client: AsyncClient, db_session: AsyncSession, student_token: str
):
    for i in range(15):
        db_session.add(
            User(
                full_name=f"Searcher {i:02d}",
                email=f"searcher{i}@unilag.edu.ng",
                password=hash_password("Pass1234"),
                department="EEE",
                level="200 Level",
                role=UserRole.STUDENT,
            )
        )
    await db_session.commit()

    resp = await client.get(
        f"{BASE}/search", params={"q": "Searcher"}, headers=auth_header(student_token)
    )
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 10


async def test_search_rejects_empty_query(client: AsyncClient, student_token: str):
    resp = await client.get(
        f"{BASE}/search", params={"q": ""}, headers=auth_header(student_token)
    )
    assert resp.status_code == 422


async def test_search_treats_wildcards_literally(client: AsyncClient, student_token: str):
    resp = await client.get(f"{BASE}/search", params={"q": "%"}, headers=auth_header(student_token))
    assert resp.status_code == 200
    assert resp.json()["data"] == []
