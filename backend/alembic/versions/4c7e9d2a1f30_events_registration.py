"""events and registration

Revision ID: 4c7e9d2a1f30
Revises: 8f2c41d9b7ae
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "4c7e9d2a1f30"
down_revision: str | Sequence[str] | None = "8f2c41d9b7ae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

event_type = postgresql.ENUM(
    "HACKATHON",
    "WORKSHOP",
    "SEMINAR",
    "CONFERENCE",
    name="eventtype",
    create_type=False,
)
registration_status = postgresql.ENUM(
    "CONFIRMED",
    "WAITLISTED",
    "CANCELLED",
    name="registrationstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'eventtype'
                ) THEN
                    CREATE TYPE eventtype AS ENUM (
                        'HACKATHON', 'WORKSHOP', 'SEMINAR', 'CONFERENCE'
                    );
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'registrationstatus'
                ) THEN
                    CREATE TYPE registrationstatus AS ENUM (
                        'CONFIRMED', 'WAITLISTED', 'CANCELLED'
                    );
                END IF;
            END
            $$;
            """
        )
    else:
        event_type.create(bind, checkfirst=True)
        registration_status.create(bind, checkfirst=True)

    with op.batch_alter_table("events") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(
            sa.Column("event_type", event_type, nullable=False, server_default="WORKSHOP")
        )
        batch_op.add_column(sa.Column("location", sa.String(length=500), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("is_virtual", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("virtual_link", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("banner_url", sa.String(length=500), nullable=True))
        batch_op.add_column(
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        )
        batch_op.add_column(
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        )
        batch_op.add_column(
            sa.Column(
                "registration_deadline",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch_op.add_column(sa.Column("max_participants", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key("fk_events_created_by_id_users", "users", ["created_by_id"], ["id"])

    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column("description", server_default=None)
        batch_op.alter_column("event_type", server_default=None)
        batch_op.alter_column("location", server_default=None)
        batch_op.alter_column("is_virtual", server_default=None)
        batch_op.alter_column("start_date", server_default=None)
        batch_op.alter_column("end_date", server_default=None)
        batch_op.alter_column("registration_deadline", server_default=None)

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS event_registrations (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                event_id VARCHAR(36) NOT NULL REFERENCES events (id),
                student_id VARCHAR(36) NOT NULL REFERENCES users (id),
                status registrationstatus NOT NULL,
                registered_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
                CONSTRAINT uq_event_registration_student UNIQUE (event_id, student_id)
            )
            """
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_event_registrations_event_id "
            "ON event_registrations (event_id)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_event_registrations_student_id "
            "ON event_registrations (student_id)"
        )
    else:
        op.create_table(
            "event_registrations",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("event_id", sa.String(length=36), nullable=False),
            sa.Column("student_id", sa.String(length=36), nullable=False),
            sa.Column("status", registration_status, nullable=False),
            sa.Column(
                "registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
            ),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
            sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_id", "student_id", name="uq_event_registration_student"),
        )
        op.create_index("ix_event_registrations_event_id", "event_registrations", ["event_id"])
        op.create_index("ix_event_registrations_student_id", "event_registrations", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_event_registrations_student_id", table_name="event_registrations")
    op.drop_index("ix_event_registrations_event_id", table_name="event_registrations")
    op.drop_table("event_registrations")

    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_constraint("fk_events_created_by_id_users", type_="foreignkey")
        for column in (
            "deleted_at",
            "max_participants",
            "registration_deadline",
            "end_date",
            "start_date",
            "banner_url",
            "virtual_link",
            "is_virtual",
            "location",
            "event_type",
            "description",
        ):
            batch_op.drop_column(column)

    bind = op.get_bind()
    registration_status.drop(bind, checkfirst=True)
    event_type.drop(bind, checkfirst=True)
