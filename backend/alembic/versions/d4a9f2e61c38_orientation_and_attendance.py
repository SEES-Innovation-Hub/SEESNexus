"""ORIENTATION event type, and attendance on registrations

Revision ID: d4a9f2e61c38
Revises: b7e2c5a91d04
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4a9f2e61c38"
down_revision: str | Sequence[str] | None = "b7e2c5a91d04"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        # ADD VALUE cannot run inside a transaction block on older Postgres.
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'ORIENTATION'")
    # SQLite stores the enum as VARCHAR with no CHECK constraint: nothing to do.

    with op.batch_alter_table("event_registrations") as batch_op:
        batch_op.add_column(sa.Column("attended_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("event_registrations") as batch_op:
        batch_op.drop_column("attended_at")
    # Postgres cannot drop an enum value. Orientations become workshops so the
    # previous code, which does not know ORIENTATION, can still read them.
    op.execute("UPDATE events SET event_type = 'WORKSHOP' WHERE event_type = 'ORIENTATION'")
