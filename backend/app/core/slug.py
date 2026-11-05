"""URL slugs for articles.

The article routes address a piece by slug rather than id (Tech Doc §5.6), and
the column is unique, so a title that repeats an existing one still has to
produce a distinct slug.
"""
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

MAX_SLUG_LENGTH = 200

_NON_WORD = re.compile(r"[^\w\s-]")
_WHITESPACE = re.compile(r"[-\s]+")


def slugify(value: str) -> str:
    """Turn a title into a lowercase, hyphenated slug.

    Non-ASCII letters are transliterated where a close equivalent exists
    (so "Ọ̀rẹ́" yields "ore") and dropped otherwise. A title made entirely of
    punctuation or non-transliterable characters would leave nothing behind, so
    the caller gets "article" instead of an empty string, and unique_slug then
    numbers it.
    """
    normalised = unicodedata.normalize("NFKD", value)
    ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
    cleaned = _NON_WORD.sub("", ascii_only).strip().lower()
    slug = _WHITESPACE.sub("-", cleaned).strip("-")[:MAX_SLUG_LENGTH].strip("-")
    return slug or "article"


async def unique_slug(db: AsyncSession, title: str, *, exclude_id: str | None = None) -> str:
    """A slug for `title` that no other article holds.

    Appends -2, -3 … until the slug is free. exclude_id lets an article keep its
    own slug when it is being renamed back to a title it already has.

    This is a check-then-insert, so two simultaneous creates with the same title
    can still collide on the unique index. The caller sees a 409 rather than a
    wrong slug, which is the safe side to fail on for an authoring flow.
    """
    # Imported here rather than at module scope: app.models imports Base from
    # app.core.database, so a top-level import would make core depend on models.
    from app.models.article import Article

    base = slugify(title)
    candidate = base
    suffix = 2

    while True:
        stmt = select(Article.id).where(Article.slug == candidate)
        if exclude_id is not None:
            stmt = stmt.where(Article.id != exclude_id)
        taken = (await db.execute(stmt)).first() is not None
        if not taken:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1
