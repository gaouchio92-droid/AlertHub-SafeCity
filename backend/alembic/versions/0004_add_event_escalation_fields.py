"""Add event escalation fields.

Revision ID: 0004_add_event_escalation_fields
Revises: 0003_create_identity_rbac_tables
Create Date: 2026-07-09 21:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_add_event_escalation_fields"
down_revision: str | None = "0003_create_identity_rbac_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add operational parsing and escalation tracking columns."""
    op.add_column("events", sa.Column("operational_data", sa.Text(), nullable=True))
    op.add_column(
        "events",
        sa.Column(
            "links",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column("events", sa.Column("escalation_priority", sa.Integer(), nullable=True))
    op.add_column("events", sa.Column("escalation_level", sa.String(length=32), nullable=True))
    op.add_column("events", sa.Column("escalation_owner", sa.String(length=255), nullable=True))
    op.add_column("events", sa.Column("escalation_due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_events_escalation_level",
        "events",
        ["escalation_level"],
        unique=False,
    )
    op.create_index(
        "ix_events_escalation_owner",
        "events",
        ["escalation_owner"],
        unique=False,
    )
    op.create_index(
        "ix_events_escalation_priority",
        "events",
        ["escalation_priority"],
        unique=False,
    )
    op.alter_column("events", "links", server_default=None)


def downgrade() -> None:
    """Remove operational parsing and escalation tracking columns."""
    op.drop_index("ix_events_escalation_priority", table_name="events")
    op.drop_index("ix_events_escalation_owner", table_name="events")
    op.drop_index("ix_events_escalation_level", table_name="events")
    op.drop_column("events", "escalation_due_at")
    op.drop_column("events", "escalation_owner")
    op.drop_column("events", "escalation_level")
    op.drop_column("events", "escalation_priority")
    op.drop_column("events", "links")
    op.drop_column("events", "operational_data")
