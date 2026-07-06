"""Create events table.

Revision ID: 0001_create_events_table
Revises:
Create Date: 2026-07-06 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_create_events_table"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create normalized events table."""
    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("problem_id", sa.String(length=255), nullable=True),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("severity", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("problem_name", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_host", "events", ["host"], unique=False)
    op.create_index("ix_events_problem_id", "events", ["problem_id"], unique=False)
    op.create_index("ix_events_severity", "events", ["severity"], unique=False)
    op.create_index("ix_events_source", "events", ["source"], unique=False)
    op.create_index("ix_events_source_started_at", "events", ["source", "started_at"], unique=False)
    op.create_index("ix_events_started_at", "events", ["started_at"], unique=False)
    op.create_index("ix_events_status", "events", ["status"], unique=False)
    op.create_index("ix_events_status_started_at", "events", ["status", "started_at"], unique=False)


def downgrade() -> None:
    """Drop normalized events table."""
    op.drop_index("ix_events_status_started_at", table_name="events")
    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_events_started_at", table_name="events")
    op.drop_index("ix_events_source_started_at", table_name="events")
    op.drop_index("ix_events_source", table_name="events")
    op.drop_index("ix_events_severity", table_name="events")
    op.drop_index("ix_events_problem_id", table_name="events")
    op.drop_index("ix_events_host", table_name="events")
    op.drop_table("events")
