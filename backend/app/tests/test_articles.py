import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/articles"


@pytest_asyncio.fixture
async def contributor_token(client: AsyncClient, db_session: AsyncSession) -> str:
    user = User(
        full_name="Chidi Contributor",
        email="chidi@unilag.edu.ng",
        password=hash_password("WriterPass1"),
        department="EEE",
        level="400 Level",
        role=UserRole.CONTRIBUTOR,
    )
    db_session.add(user)
    await db_session.commit()
    resp = await client.post("/api/v1/auth/login", json={"email": user.email, "password": "WriterPass1"})
    return resp.json()["data"]["access_token"]


def article_payload(**overrides) -> dict:
    payload = {
        "title": "FloodGuard wins at the IEEE IES SYP Congress",
        "content": "## The build\n\nSensors, a LoRa link and a lot of coffee.",
        "summary": "How a SEES team took first place.",
        "status": "PUBLISHED",
    }
    payload.update(overrides)
    return payload


async def create_article(client: AsyncClient, token: str, **overrides) -> dict:
    response = await client.post(BASE, json=article_payload(**overrides), headers=auth_header(token))
    assert response.status_code == 201, response.text
    return response.json()["data"]


# --- create ---


async def test_contributors_and_admins_can_write_students_cannot(
    client: AsyncClient, contributor_token: str, admin_token: str, student_token: str
):
    by_contributor = await create_article(client, contributor_token)
    assert by_contributor["slug"] == "floodguard-wins-at-the-ieee-ies-syp-congress"
    assert by_contributor["author"]["full_name"] == "Chidi Contributor"
    assert "email" not in by_contributor["author"]
    assert by_contributor["published_at"] is not None

    await create_article(client, admin_token, title="Admin note")

    forbidden = await client.post(BASE, json=article_payload(), headers=auth_header(student_token))
    assert forbidden.status_code == 403
    assert (await client.post(BASE, json=article_payload())).status_code == 401


async def test_slugs_are_unique_and_validated(client: AsyncClient, contributor_token: str):
    first = await create_article(client, contributor_token, title="Week 1: Café & Circuits!")
    second = await create_article(client, contributor_token, title="Week 1: Café & Circuits!")
    assert first["slug"] == "week-1-cafe-circuits"
    assert second["slug"] == "week-1-cafe-circuits-2"

    custom = await create_article(client, contributor_token, slug="my-custom-slug")
    assert custom["slug"] == "my-custom-slug"
    clash = await client.post(
        BASE, json=article_payload(slug="my-custom-slug"), headers=auth_header(contributor_token)
    )
    assert clash.status_code == 409

    bad = await client.post(
        BASE, json=article_payload(slug="Not A Slug"), headers=auth_header(contributor_token)
    )
    assert bad.status_code == 422


async def test_new_articles_default_to_draft(client: AsyncClient, contributor_token: str):
    payload = article_payload()
    del payload["status"]
    response = await client.post(BASE, json=payload, headers=auth_header(contributor_token))
    assert response.json()["data"]["status"] == "DRAFT"
    assert response.json()["data"]["published_at"] is None


# --- list and read ---


async def test_list_shows_published_only_to_members(
    client: AsyncClient, contributor_token: str, student_token: str, admin_token: str
):
    await create_article(client, contributor_token, title="Live")
    await create_article(client, contributor_token, title="Secret draft", status="DRAFT")

    assert (await client.get(BASE)).status_code == 401

    student_view = await client.get(BASE, headers=auth_header(student_token))
    body = student_view.json()["data"]
    assert [a["title"] for a in body["items"]] == ["Live"]
    assert body["total"] == 1
    # List rows leave the body out; the detail route has it.
    assert "content" not in body["items"][0]

    # Asking for drafts does not reveal other people's drafts.
    sneaky = await client.get(f"{BASE}?status=DRAFT", headers=auth_header(student_token))
    assert sneaky.json()["data"]["total"] == 0

    # The author sees their own drafts with mine=true.
    own = await client.get(f"{BASE}?mine=true", headers=auth_header(contributor_token))
    assert {a["title"] for a in own.json()["data"]["items"]} == {"Live", "Secret draft"}

    # Admins see everything.
    admin_view = await client.get(BASE, headers=auth_header(admin_token))
    assert admin_view.json()["data"]["total"] == 2


async def test_search_and_pagination(client: AsyncClient, contributor_token: str, student_token: str):
    for title in ("Verifact launch", "BAER system update", "Verifact v2"):
        await create_article(client, contributor_token, title=title)

    found = await client.get(f"{BASE}?search=verifact", headers=auth_header(student_token))
    assert {a["title"] for a in found.json()["data"]["items"]} == {"Verifact launch", "Verifact v2"}

    paged = await client.get(f"{BASE}?page=2&page_size=2", headers=auth_header(student_token))
    data = paged.json()["data"]
    assert (data["total"], data["total_pages"], len(data["items"])) == (3, 2, 1)


async def test_get_by_id_or_slug_and_draft_privacy(
    client: AsyncClient, contributor_token: str, student_token: str, admin_token: str
):
    article = await create_article(client, contributor_token)
    by_id = await client.get(f"{BASE}/{article['id']}", headers=auth_header(student_token))
    by_slug = await client.get(f"{BASE}/{article['slug']}", headers=auth_header(student_token))
    assert by_id.status_code == by_slug.status_code == 200
    assert by_slug.json()["data"]["content"].startswith("## The build")
    assert (await client.get(f"{BASE}/{article['id']}")).status_code == 401

    draft = await create_article(client, contributor_token, title="Draft", status="DRAFT")
    hidden = await client.get(f"{BASE}/{draft['id']}", headers=auth_header(student_token))
    assert hidden.status_code == 404
    assert hidden.json()["message"] == "Article not found"
    for token in (contributor_token, admin_token):
        assert (await client.get(f"{BASE}/{draft['id']}", headers=auth_header(token))).status_code == 200

    assert (await client.get(f"{BASE}/nope", headers=auth_header(student_token))).status_code == 404


# --- edit ---


async def test_author_and_admin_can_edit_others_cannot(
    client: AsyncClient, contributor_token: str, admin_token: str, student_token: str
):
    article = await create_article(client, contributor_token)

    edited = await client.put(
        f"{BASE}/{article['id']}", json={"title": "New title"}, headers=auth_header(contributor_token)
    )
    assert edited.status_code == 200
    # The slug stays put so links already shared keep working.
    assert edited.json()["data"]["slug"] == article["slug"]

    by_admin = await client.put(
        f"{BASE}/{article['slug']}", json={"summary": "Tightened"}, headers=auth_header(admin_token)
    )
    assert by_admin.status_code == 200

    denied = await client.put(
        f"{BASE}/{article['id']}", json={"title": "Hijack"}, headers=auth_header(student_token)
    )
    assert denied.status_code == 403

    null_title = await client.put(
        f"{BASE}/{article['id']}", json={"title": None}, headers=auth_header(contributor_token)
    )
    assert null_title.status_code == 400


async def test_publishing_sets_published_at_once(client: AsyncClient, contributor_token: str):
    draft = await create_article(client, contributor_token, status="DRAFT")
    published = await client.put(
        f"{BASE}/{draft['id']}", json={"status": "PUBLISHED"}, headers=auth_header(contributor_token)
    )
    first_published_at = published.json()["data"]["published_at"]
    assert first_published_at is not None

    await client.put(
        f"{BASE}/{draft['id']}", json={"status": "DRAFT"}, headers=auth_header(contributor_token)
    )
    again = await client.put(
        f"{BASE}/{draft['id']}", json={"status": "PUBLISHED"}, headers=auth_header(contributor_token)
    )
    assert again.json()["data"]["published_at"] == first_published_at


async def test_changing_slug_checks_for_clashes(client: AsyncClient, contributor_token: str):
    one = await create_article(client, contributor_token, title="One")
    await create_article(client, contributor_token, title="Two")
    headers = auth_header(contributor_token)
    clash = await client.put(f"{BASE}/{one['id']}", json={"slug": "two"}, headers=headers)
    assert clash.status_code == 409
    ok = await client.put(f"{BASE}/{one['id']}", json={"slug": "uno"}, headers=headers)
    assert ok.json()["data"]["slug"] == "uno"


# --- delete ---


async def test_delete_is_soft_and_restricted(
    client: AsyncClient, contributor_token: str, admin_token: str, student_token: str
):
    article = await create_article(client, contributor_token)
    assert (
        await client.delete(f"{BASE}/{article['id']}", headers=auth_header(student_token))
    ).status_code == 403
    assert (await client.delete(f"{BASE}/{article['id']}")).status_code == 401

    deleted = await client.delete(f"{BASE}/{article['id']}", headers=auth_header(contributor_token))
    assert deleted.status_code == 200
    assert (
        await client.get(f"{BASE}/{article['id']}", headers=auth_header(admin_token))
    ).status_code == 404

    # Gone from the dashboard count too.
    dashboard = await client.get("/api/v1/admin/dashboard", headers=auth_header(admin_token))
    assert dashboard.json()["data"]["total_articles"] == 0

    # The deleted row keeps its slug, so a new article with the same title gets "-2".
    replacement = await create_article(client, contributor_token)
    assert replacement["slug"] == f"{article['slug']}-2"
