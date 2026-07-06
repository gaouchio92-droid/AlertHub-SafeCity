"""Event persistence model."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Event(Base):
    """Normalized event stored from any connector source."""

    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("source", "problem_id", name="uq_events_source_problem_id"),
        Index("ix_events_source_started_at", "source", "started_at"),
        Index("ix_events_status_started_at", "status", "started_at"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    problem_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    host: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    severity: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    problem_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
