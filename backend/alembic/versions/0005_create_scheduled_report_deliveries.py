"""Create scheduled report delivery tracking table.

Revision ID: 0005_report_delivery
Revises: 0004_add_event_escalation_fields
Create Date: 2026-07-10 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_report_delivery"
down_revision: str | None = "0004_add_event_escalation_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create scheduled report delivery tracking table."""
    op.create_table(
        "scheduled_report_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_kind", sa.String(length=32), nullable=False),
        sa.Column("channel_id", sa.String(length=64), nullable=False),
        sa.Column("message_id", sa.String(length=64), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scheduled_report_deliveries_report_kind",
        "scheduled_report_deliveries",
        ["report_kind"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_report_deliveries_sent_at",
        "scheduled_report_deliveries",
        ["sent_at"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_report_deliveries_status",
        "scheduled_report_deliveries",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_report_delivery_kind_sent",
        "scheduled_report_deliveries",
        ["report_kind", "sent_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop scheduled report delivery tracking table."""
    op.drop_index(
        "ix_scheduled_report_delivery_kind_sent",
        table_name="scheduled_report_deliveries",
    )
    op.drop_index(
        "ix_scheduled_report_deliveries_status",
        table_name="scheduled_report_deliveries",
    )
    op.drop_index(
        "ix_scheduled_report_deliveries_sent_at",
        table_name="scheduled_report_deliveries",
    )
    op.drop_index(
        "ix_scheduled_report_deliveries_report_kind",
        table_name="scheduled_report_deliveries",
    )
    op.drop_table("scheduled_report_deliveries")
