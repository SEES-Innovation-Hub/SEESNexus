"""rate limits, code attempts and purpose, password_changed_at

Revision ID: f1b6d2c84a57
Revises: e8c3a7d15b92
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f1b6d2c84a57"
down_revision: str | Sequence[str] | None = "e8c3a7d15b92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("verification_codes") as batch_op:
        batch_op.add_column(sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
        # Existing codes were all registration codes.
        batch_op.add_column(
            sa.Column("purpose", sa.String(length=32), nullable=False, server_default="REGISTER")
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "rate_limit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rate_limit_events_key_created_at", "rate_limit_events", ["key", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_rate_limit_events_key_created_at", table_name="rate_limit_events")
    op.drop_table("rate_limit_events")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("password_changed_at")
    with op.batch_alter_table("verification_codes") as batch_op:
        batch_op.drop_column("purpose")
        batch_op.drop_column("attempts")
