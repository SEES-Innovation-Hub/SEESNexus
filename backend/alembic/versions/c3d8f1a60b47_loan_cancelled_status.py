"""add CANCELLED to loanstatus

Revision ID: c3d8f1a60b47
Revises: a1b4e7c90d62

Lets a borrower withdraw their own pending request, recorded distinctly from an
admin's rejection.

The two dialects need different work. On Postgres the enum is a real type and
gains a label; ALTER TYPE ... ADD VALUE is transactional from PG 12 onward, and
Tech Doc §3 mandates PG 15+. On SQLite, SQLAlchemy renders Enum as VARCHAR with
a CHECK constraint, so the column has to be rebuilt through batch_alter_table
for the new value to be accepted.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d8f1a60b47"
down_revision: str | Sequence[str] | None = "a1b4e7c90d62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_VALUES = ("PENDING", "APPROVED", "RETURNED", "REJECTED")
NEW_VALUES = (*OLD_VALUES, "CANCELLED")


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE loanstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")
        return

    with op.batch_alter_table("hardware_loans") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum(*OLD_VALUES, name="loanstatus"),
            type_=sa.Enum(*NEW_VALUES, name="loanstatus"),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Lossy by necessity, and it refuses rather than guessing.

    Postgres cannot remove a label from an enum in place; the type has to be
    recreated. Either way, any row already CANCELLED has no correct home in the
    old set -- mapping it to REJECTED would rewrite a student's withdrawal as an
    admin's refusal, which is exactly the distinction this migration added.

    So the downgrade stops if such rows exist and leaves the operator to decide.
    """
    bind = op.get_bind()

    cancelled = bind.execute(
        sa.text("SELECT count(*) FROM hardware_loans WHERE status = 'CANCELLED'")
    ).scalar_one()
    if cancelled:
        raise RuntimeError(
            f"{cancelled} loan(s) have status CANCELLED, which does not exist in the "
            "previous enum. Decide what they should become (REJECTED misrepresents "
            "them as admin refusals) and update them before downgrading."
        )

    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE loanstatus RENAME TO loanstatus_old")
        sa.Enum(*OLD_VALUES, name="loanstatus").create(bind)
        op.execute(
            "ALTER TABLE hardware_loans "
            "ALTER COLUMN status TYPE loanstatus USING status::text::loanstatus"
        )
        op.execute("DROP TYPE loanstatus_old")
        return

    with op.batch_alter_table("hardware_loans") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum(*NEW_VALUES, name="loanstatus"),
            type_=sa.Enum(*OLD_VALUES, name="loanstatus"),
            existing_nullable=False,
        )
