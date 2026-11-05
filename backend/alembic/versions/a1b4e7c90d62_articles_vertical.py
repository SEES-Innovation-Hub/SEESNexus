"""articles vertical

Revision ID: a1b4e7c90d62
Revises: 4c7e9d2a1f30

Hand-written, like 8f2c41d9b7ae and 4c7e9d2a1f30: alembic/env.py sets no
render_as_batch, so autogenerate emits SQLite-hostile ALTER TABLE output for a
change of this shape.

The initial schema created `articles` with four columns (id, title, author_id,
created_at) as a stand-in so the admin dashboard could count real rows. This
brings the table up to the full Tech Doc §4.2 shape, plus deleted_at, which §4.3
requires in substance because a user's articles must never be hard-deleted.

Existing rows get a slug derived from their title. The column is unique, so the
backfill numbers duplicates rather than leaving every row with the same value.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b4e7c90d62"
down_revision: str | Sequence[str] | None = "4c7e9d2a1f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

article_status = sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="articlestatus")


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'articlestatus'
                ) THEN
                    CREATE TYPE articlestatus AS ENUM (
                        'DRAFT', 'PUBLISHED', 'ARCHIVED'
                    );
                END IF;
            END
            $$;
            """
        )
    else:
        article_status.create(bind, checkfirst=True)

    # slug is added nullable so existing rows can be backfilled before the
    # NOT NULL constraint and the unique index go on.
    with op.batch_alter_table("articles") as batch_op:
        batch_op.add_column(sa.Column("slug", sa.String(length=280), nullable=True))
        batch_op.add_column(
            sa.Column("content", sa.Text(), nullable=False, server_default="")
        )
        batch_op.add_column(sa.Column("excerpt", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("cover_image_url", sa.String(length=500), nullable=True))
        batch_op.add_column(
            sa.Column(
                "status",
                article_status,
                nullable=False,
                server_default="DRAFT",
            )
        )
        batch_op.add_column(
            sa.Column("tags", sa.JSON(), nullable=False, server_default="[]")
        )
        batch_op.add_column(sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    _backfill_slugs(bind)

    with op.batch_alter_table("articles") as batch_op:
        batch_op.alter_column("slug", existing_type=sa.String(length=280), nullable=False)
        batch_op.create_index("ix_articles_slug", ["slug"], unique=True)
        # The stand-in table stored author_id without a foreign key.
        batch_op.create_foreign_key(
            "fk_articles_author_id_users", "users", ["author_id"], ["id"]
        )


def _backfill_slugs(bind) -> None:
    """Give every existing row a unique slug derived from its title.

    The logic is duplicated from app/core/slug.py rather than imported. A
    migration has to keep producing the same output forever, and importing
    application code would let a later refactor of slugify() silently change
    what this historical migration does.

    It must still *match* app/core/slug.py today, including the NFKD
    transliteration: without it a title like "Ampères & Ohms" backfills as
    "ampères-ohms" while the running app would generate "amperes-ohms", leaving
    non-ASCII slugs in URLs and two different slugs for the same title.
    """
    import re
    import unicodedata

    rows = bind.execute(sa.text("SELECT id, title FROM articles")).fetchall()
    seen: set[str] = set()

    for row in rows:
        normalised = unicodedata.normalize("NFKD", row.title or "")
        ascii_only = normalised.encode("ascii", "ignore").decode("ascii")
        base = re.sub(r"[^\w\s-]", "", ascii_only).strip().lower()
        base = re.sub(r"[-\s]+", "-", base).strip("-")[:200].strip("-") or "article"

        candidate = base
        suffix = 2
        while candidate in seen:
            candidate = f"{base}-{suffix}"
            suffix += 1
        seen.add(candidate)

        bind.execute(
            sa.text("UPDATE articles SET slug = :slug WHERE id = :id"),
            {"slug": candidate, "id": row.id},
        )


def downgrade() -> None:
    bind = op.get_bind()

    with op.batch_alter_table("articles") as batch_op:
        batch_op.drop_constraint("fk_articles_author_id_users", type_="foreignkey")
        batch_op.drop_index("ix_articles_slug")
        for column in (
            "deleted_at",
            "updated_at",
            "published_at",
            "tags",
            "status",
            "cover_image_url",
            "excerpt",
            "content",
            "slug",
        ):
            batch_op.drop_column(column)

    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS articlestatus")
    else:
        article_status.drop(bind, checkfirst=True)
