import pytest
from httpx import AsyncClient

from app.core.slug import slugify
from app.models.user import User
from app.tests.conftest import auth_header

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/articles"


def article_payload(**overrides) -> dict:
    payload = {
        "title": "Designing a Low-Power Sensor Node",
        "content": "A walk through the power budget of a battery-driven sensor node.",
        "excerpt": "Power budgets, in practice.",
        "tags": ["embedded", "power"],
    }
    payload.update(overrides)
    return payload


async def create_article(client: AsyncClient, token: str, **overrides) -> dict:
    response = await client.post(BASE, json=article_payload(**overrides), headers=auth_header(token))
    assert response.status_code == 201, response.text
    return response.json()["data"]


# --- POST /articles (§5.6: contributor/admin) ---


async def test_contributor_creates_a_draft(client: AsyncClient, contributor_token: str):
    article = await create_article(client, contributor_token)
    assert article["status"] == "DRAFT"
    assert article["slug"] == "designing-a-low-power-sensor-node"
    assert article["published_at"] is None
    assert article["tags"] == ["embedded", "power"]


async def test_admin_may_also_create(client: AsyncClient, admin_token: str):
    article = await create_article(client, admin_token)
    assert article["status"] == "DRAFT"


async def test_create_is_refused_to_students_and_strangers(
    client: AsyncClient, student_token: str
):
    forbidden = await client.post(
        BASE, json=article_payload(), headers=auth_header(student_token)
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["status"] == "error"

    assert (await client.post(BASE, json=article_payload())).status_code == 401


async def test_author_id_comes_from_the_token_not_the_body(
    client: AsyncClient, contributor_token: str, contributor_user: User, admin_user: User
):
    response = await client.post(
        BASE,
        json=article_payload(author_id=admin_user.id),
        headers=auth_header(contributor_token),
    )
    assert response.status_code == 201
    assert response.json()["data"]["author_id"] == contributor_user.id


async def test_creating_as_published_stamps_published_at(
    client: AsyncClient, contributor_token: str
):
    article = await create_article(client, contributor_token, status="PUBLISHED")
    assert article["status"] == "PUBLISHED"
    assert article["published_at"] is not None


# --- slugs ---


async def test_duplicate_titles_get_distinct_slugs(client: AsyncClient, contributor_token: str):
    first = await create_article(client, contributor_token)
    second = await create_article(client, contributor_token)
    third = await create_article(client, contributor_token)
    assert first["slug"] == "designing-a-low-power-sensor-node"
    assert second["slug"] == "designing-a-low-power-sensor-node-2"
    assert third["slug"] == "designing-a-low-power-sensor-node-3"


async def test_slugify_handles_punctuation_and_accents():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("  spaced   out  ") == "spaced-out"
    assert slugify("Ampères & Ohms") == "amperes-ohms"
    # Nothing survives transliteration, so the caller still gets a usable slug.
    assert slugify("!!!") == "article"
    assert slugify("") == "article"


async def test_renaming_an_article_moves_its_slug(client: AsyncClient, contributor_token: str):
    article = await create_article(client, contributor_token)
    renamed = await client.put(
        f"{BASE}/{article['slug']}",
        json={"title": "A Completely Different Title"},
        headers=auth_header(contributor_token),
    )
    assert renamed.status_code == 200
    assert renamed.json()["data"]["slug"] == "a-completely-different-title"


# --- GET /articles (public, published only) ---


async def test_list_shows_published_and_hides_drafts(
    client: AsyncClient, contributor_token: str
):
    await create_article(client, contributor_token, title="A Draft Piece")
    published = await create_article(
        client, contributor_token, title="A Published Piece", status="PUBLISHED"
    )

    listing = await client.get(BASE)
    assert listing.status_code == 200
    body = listing.json()
    assert body["status"] == "success"
    assert body["data"]["total"] == 1
    assert [item["slug"] for item in body["data"]["items"]] == [published["slug"]]


async def test_list_hides_archived_articles(client: AsyncClient, contributor_token: str):
    article = await create_article(client, contributor_token, status="PUBLISHED")
    assert (await client.get(BASE)).json()["data"]["total"] == 1

    archived = await client.put(
        f"{BASE}/{article['slug']}",
        json={"status": "ARCHIVED"},
        headers=auth_header(contributor_token),
    )
    assert archived.status_code == 200
    assert (await client.get(BASE)).json()["data"]["total"] == 0


async def test_list_is_paginated_and_filterable_by_author(
    client: AsyncClient, contributor_token: str, other_contributor_token: str,
    contributor_user: User,
):
    await create_article(client, contributor_token, title="Mine", status="PUBLISHED")
    await create_article(client, other_contributor_token, title="Theirs", status="PUBLISHED")

    everything = await client.get(f"{BASE}?page=1&page_size=10")
    assert everything.json()["data"]["total"] == 2

    mine = await client.get(f"{BASE}?author_id={contributor_user.id}")
    assert [item["title"] for item in mine.json()["data"]["items"]] == ["Mine"]


async def test_list_can_filter_by_tag(client: AsyncClient, contributor_token: str):
    await create_article(
        client, contributor_token, title="Tagged", status="PUBLISHED", tags=["rf"]
    )
    await create_article(
        client, contributor_token, title="Untagged", status="PUBLISHED", tags=["power"]
    )

    filtered = await client.get(f"{BASE}?tag=rf")
    assert [item["title"] for item in filtered.json()["data"]["items"]] == ["Tagged"]


# --- GET /articles/{slug} ---


async def test_published_article_is_public(client: AsyncClient, contributor_token: str):
    article = await create_article(client, contributor_token, status="PUBLISHED")
    response = await client.get(f"{BASE}/{article['slug']}")
    assert response.status_code == 200
    assert response.json()["data"]["slug"] == article["slug"]


async def test_draft_is_visible_to_its_author_and_admins_only(
    client: AsyncClient, contributor_token: str, other_contributor_token: str, admin_token: str
):
    article = await create_article(client, contributor_token)
    url = f"{BASE}/{article['slug']}"

    assert (await client.get(url, headers=auth_header(contributor_token))).status_code == 200
    assert (await client.get(url, headers=auth_header(admin_token))).status_code == 200

    # 404 rather than 403: the slug is derived from the title, so a stranger
    # must not learn that a draft exists at it.
    assert (await client.get(url)).status_code == 404
    stranger = await client.get(url, headers=auth_header(other_contributor_token))
    assert stranger.status_code == 404


async def test_unknown_slug_returns_enveloped_404(client: AsyncClient):
    response = await client.get(f"{BASE}/no-such-article")
    assert response.status_code == 404
    assert response.json() == {"status": "error", "message": "Article not found", "data": None}


# --- PUT /articles/{slug} (author or admin) ---


async def test_author_updates_their_own_article(client: AsyncClient, contributor_token: str):
    article = await create_article(client, contributor_token)
    response = await client.put(
        f"{BASE}/{article['slug']}",
        json={"content": "Rewritten from scratch.", "tags": ["embedded"]},
        headers=auth_header(contributor_token),
    )
    assert response.status_code == 200
    assert response.json()["data"]["content"] == "Rewritten from scratch."
    assert response.json()["data"]["tags"] == ["embedded"]


async def test_admin_may_update_someone_elses_article(
    client: AsyncClient, contributor_token: str, admin_token: str
):
    article = await create_article(client, contributor_token)
    response = await client.put(
        f"{BASE}/{article['slug']}",
        json={"title": "Edited By An Admin"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200


async def test_another_contributor_cannot_update_or_delete(
    client: AsyncClient, contributor_token: str, other_contributor_token: str, student_token: str
):
    article = await create_article(client, contributor_token, status="PUBLISHED")
    url = f"{BASE}/{article['slug']}"

    assert (
        await client.put(url, json={"title": "Hijacked"}, headers=auth_header(other_contributor_token))
    ).status_code == 403
    assert (
        await client.delete(url, headers=auth_header(other_contributor_token))
    ).status_code == 403

    # A student is stopped earlier, by the role gate.
    assert (
        await client.put(url, json={"title": "Nope"}, headers=auth_header(student_token))
    ).status_code == 403
    assert (await client.put(url, json={"title": "Nope"})).status_code == 401
    assert (await client.delete(url)).status_code == 401


async def test_published_at_is_stamped_once_and_never_moved(
    client: AsyncClient, contributor_token: str
):
    article = await create_article(client, contributor_token)
    assert article["published_at"] is None

    published = await client.put(
        f"{BASE}/{article['slug']}",
        json={"status": "PUBLISHED"},
        headers=auth_header(contributor_token),
    )
    first_stamp = published.json()["data"]["published_at"]
    assert first_stamp is not None

    edited = await client.put(
        f"{BASE}/{article['slug']}",
        json={"content": "A later correction."},
        headers=auth_header(contributor_token),
    )
    assert edited.json()["data"]["published_at"] == first_stamp

    # Archiving and republishing must not move it either.
    await client.put(
        f"{BASE}/{article['slug']}",
        json={"status": "ARCHIVED"},
        headers=auth_header(contributor_token),
    )
    republished = await client.put(
        f"{BASE}/{article['slug']}",
        json={"status": "PUBLISHED"},
        headers=auth_header(contributor_token),
    )
    assert republished.json()["data"]["published_at"] == first_stamp


async def test_tags_are_capped_and_cleaned(client: AsyncClient, contributor_token: str):
    article = await create_article(
        client, contributor_token, tags=["  rf  ", "rf", "", "power"]
    )
    # Stripped, de-duplicated, blanks dropped.
    assert article["tags"] == ["rf", "power"]

    too_many = await client.post(
        BASE,
        json=article_payload(title="Too Many Tags", tags=[f"tag{i}" for i in range(11)]),
        headers=auth_header(contributor_token),
    )
    assert too_many.status_code == 422
    assert too_many.json()["status"] == "error"


# --- DELETE /articles/{slug} ---


async def test_delete_soft_deletes(client: AsyncClient, contributor_token: str):
    article = await create_article(client, contributor_token, status="PUBLISHED")
    deleted = await client.delete(
        f"{BASE}/{article['slug']}", headers=auth_header(contributor_token)
    )
    assert deleted.status_code == 200

    assert (await client.get(f"{BASE}/{article['slug']}")).status_code == 404
    assert (await client.get(BASE)).json()["data"]["total"] == 0

    # Gone from the API, but still editable by nobody -- the row survives, which
    # is what §4.3 requires.
    again = await client.delete(
        f"{BASE}/{article['slug']}", headers=auth_header(contributor_token)
    )
    assert again.status_code == 404


async def test_dashboard_counts_only_live_articles(
    client: AsyncClient, contributor_token: str, admin_token: str
):
    article = await create_article(client, contributor_token, status="PUBLISHED")

    before = await client.get("/api/v1/admin/dashboard", headers=auth_header(admin_token))
    assert before.json()["data"]["total_articles"] == 1

    await client.delete(f"{BASE}/{article['slug']}", headers=auth_header(contributor_token))

    after = await client.get("/api/v1/admin/dashboard", headers=auth_header(admin_token))
    assert after.json()["data"]["total_articles"] == 0
