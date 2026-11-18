"""articles vertical, and CANCELLED loan status

Revision ID: b7e2c5a91d04
Revises: 4c7e9d2a1f30

Articles: the initial schema created a stand-in table (id, title, author_id,
created_at) with no routes, so it should be empty. Any rows that do exist are
kept: they get their id as slug, empty content, and DRAFT status, so nothing
half-made is shown to members.

Loans: adds CANCELLED, for a borrower withdrawing a pending request.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b7e2c5a91d04"
down_revision: str | Sequence[str] | None = "4c7e9d2a1f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

article_status = postgresql.ENUM("DRAFT", "PUBLISHED", name="articlestatus", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # --- loans -----------------------------------------------------------
    if is_pg:
        # ADD VALUE cannot run inside a transaction block on older Postgres.
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE loanstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")
    # SQLite stores the enum as VARCHAR without a CHECK constraint
    # (SQLAlchemy's create_constraint defaults to False), so nothing to do.

    # --- articles --------------------------------------------------------
    if is_pg:
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'articlestatus') THEN
                    CREATE TYPE articlestatus AS ENUM ('DRAFT', 'PUBLISHED');
                END IF;
            END
            $$;
            """
        )
    else:
        article_status.create(bind, checkfirst=True)

    with op.batch_alter_table("articles") as batch_op:
        batch_op.add_column(sa.Column("slug", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("summary", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("content", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("cover_image_url", sa.String(length=500), nullable=True))
        batch_op.add_column(
            sa.Column("status", article_status, nullable=False, server_default="DRAFT")
        )
        batch_op.add_column(
            sa.Column(
                "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
            )
        )
        batch_op.add_column(sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE articles SET slug = id WHERE slug IS NULL")

    with op.batch_alter_table("articles") as batch_op:
        batch_op.alter_column("slug", existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column("content", server_default=None)
        batch_op.alter_column("status", server_default=None)
        batch_op.create_index("ix_articles_slug", ["slug"], unique=True)
        batch_op.create_foreign_key("fk_articles_author_id_users", "users", ["author_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("articles") as batch_op:
        batch_op.drop_constraint("fk_articles_author_id_users", type_="foreignkey")
        batch_op.drop_index("ix_articles_slug")
        for column in (
            "deleted_at",
            "published_at",
            "updated_at",
            "status",
            "cover_image_url",
            "content",
            "summary",
            "slug",
        ):
            batch_op.drop_column(column)

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS articlestatus")
    # Postgres cannot drop a value from an enum. Withdrawn requests are folded
    # into REJECTED so the old code, which does not know CANCELLED, can read them;
    # the unused label stays on the type.
    op.execute("UPDATE hardware_loans SET status = 'REJECTED' WHERE status = 'CANCELLED'")
