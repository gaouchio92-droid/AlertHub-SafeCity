"""Scheduled report delivery tracking models."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ScheduledReportDelivery(Base):
    """Persist automatic report delivery attempts to avoid duplicate sends."""

    __tablename__ = "scheduled_report_deliveries"
    __table_args__ = (
        Index("ix_scheduled_report_delivery_kind_sent", "report_kind", "sent_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    report_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    channel_id: Mapped[str] = mapped_column(String(64), nullable=False)
    message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
