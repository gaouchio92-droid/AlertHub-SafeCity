"""Add events deduplication constraint.

Revision ID: 0002_add_events_dedup_constraint
Revises: 0001_create_events_table
Create Date: 2026-07-06 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_add_events_dedup_constraint"
down_revision: str | None = "0001_create_events_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add idempotency key for connector events."""
    op.create_unique_constraint(
        "uq_events_source_problem_id",
        "events",
        ["source", "problem_id"],
    )


def downgrade() -> None:
    """Remove idempotency key for connector events."""
    op.drop_constraint("uq_events_source_problem_id", "events", type_="unique")
