"""self check-in code on events

Revision ID: e8c3a7d15b92
Revises: d4a9f2e61c38
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e8c3a7d15b92"
down_revision: str | Sequence[str] | None = "d4a9f2e61c38"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(sa.Column("checkin_code", sa.String(length=12), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_column("checkin_code")
