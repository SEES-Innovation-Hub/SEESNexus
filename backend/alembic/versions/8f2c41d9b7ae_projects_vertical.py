"""projects vertical

Revision ID: 8f2c41d9b7ae
Revises: 221aa704778c
Create Date: 2026-09-15 00:00:00.000000

Hand-written: alembic/env.py sets no render_as_batch, so autogenerate emits
SQLite-hostile ALTER TABLE output for this change.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8f2c41d9b7ae'
down_revision: str | Sequence[str] | None = '221aa704778c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

project_status = sa.Enum('IDEATION', 'IN_PROGRESS', 'COMPLETED', name='projectstatus')
project_category = sa.Enum('IOT', 'AI_ML', 'EMBEDDED', 'WEB', 'MOBILE', name='projectcategory')


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # op.add_column does NOT create the enum type the way create_table does,
    # so both types are created up front or Postgres fails on first add_column.
    project_status.create(bind, checkfirst=True)
    project_category.create(bind, checkfirst=True)

    # server_default on the non-nullable columns: the stub table may already
    # hold rows, which have no value for them. Defaults are dropped afterwards
    # so the application supplies every value from here on.
    with op.batch_alter_table('projects') as batch_op:
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=False, server_default=''))
        batch_op.add_column(
            sa.Column('tech_stack', sa.JSON(), nullable=False, server_default='[]')
        )
        batch_op.add_column(sa.Column('github_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('demo_url', sa.String(length=500), nullable=True))
        batch_op.add_column(
            sa.Column('status', project_status, nullable=False, server_default='IDEATION')
        )
        batch_op.add_column(
            sa.Column('category', project_category, nullable=False, server_default='WEB')
        )
        batch_op.add_column(sa.Column('thumbnail_url', sa.String(length=500), nullable=True))
        batch_op.add_column(
            sa.Column(
                'updated_at',
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        # The stub column had no FK; SQLite needs the table rebuild batch mode
        # provides to add one.
        batch_op.create_foreign_key('fk_projects_created_by_id_users', 'users', ['created_by_id'], ['id'])

    with op.batch_alter_table('projects') as batch_op:
        batch_op.alter_column('description', server_default=None)
        batch_op.alter_column('tech_stack', server_default=None)
        batch_op.alter_column('status', server_default=None)
        batch_op.alter_column('category', server_default=None)

    op.create_table(
        'project_members',
        sa.Column('project_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('project_id', 'user_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('project_members')

    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_constraint('fk_projects_created_by_id_users', type_='foreignkey')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('thumbnail_url')
        batch_op.drop_column('category')
        batch_op.drop_column('status')
        batch_op.drop_column('demo_url')
        batch_op.drop_column('github_url')
        batch_op.drop_column('tech_stack')
        batch_op.drop_column('description')

    # Columns are gone, so the types are now unreferenced and safe to drop.
    bind = op.get_bind()
    project_category.drop(bind, checkfirst=True)
    project_status.drop(bind, checkfirst=True)
