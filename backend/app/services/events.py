"""Event query services."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.event import Event


class EventService:
    """Read normalized events from the local AlertHub database."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_events(
        self,
        *,
        limit: int,
        offset: int,
        source: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> tuple[list[Event], int]:
        """Return paginated events ordered by newest first."""
        statement = self._base_query(source=source, status=status, severity=severity)
        total = self._db.scalar(
            select(func.count()).select_from(statement.subquery())
        )
        events = self._db.scalars(
            statement.order_by(Event.started_at.desc().nullslast(), Event.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return list(events), total or 0

    @staticmethod
    def _base_query(
        *,
        source: str | None,
        status: str | None,
        severity: str | None,
    ) -> Select[tuple[Event]]:
        statement = select(Event)
        if source:
            statement = statement.where(Event.source == source)
        if status:
            statement = statement.where(Event.status == status)
        if severity:
            statement = statement.where(Event.severity == severity)
        return statement
