"""Event query services."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorEvent
from app.models.event import Event


class EventIngestionResult:
    """Event ingestion counters."""

    def __init__(self, *, received: int, created: int, updated: int) -> None:
        self.received = received
        self.created = created
        self.updated = updated


class EventService:
    """Read and write normalized events in the local AlertHub database."""

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

    def upsert_connector_events(
        self,
        connector_events: list[ConnectorEvent],
    ) -> EventIngestionResult:
        """Persist connector events using source and problem_id as the idempotency key."""
        created = 0
        updated = 0

        for connector_event in connector_events:
            event = self._find_existing_event(connector_event)
            if event is None:
                self._db.add(self._build_event(connector_event))
                created += 1
                continue

            self._apply_connector_event(event, connector_event)
            updated += 1

        self._db.commit()
        return EventIngestionResult(
            received=len(connector_events),
            created=created,
            updated=updated,
        )

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

    def _find_existing_event(self, connector_event: ConnectorEvent) -> Event | None:
        if not connector_event.problem_id:
            return None
        return self._db.scalar(
            select(Event).where(
                Event.source == connector_event.source,
                Event.problem_id == connector_event.problem_id,
            )
        )

    @staticmethod
    def _build_event(connector_event: ConnectorEvent) -> Event:
        return Event(
            source=connector_event.source,
            problem_id=connector_event.problem_id,
            host=connector_event.host,
            severity=connector_event.severity,
            status=connector_event.status,
            problem_name=connector_event.problem_name,
            started_at=connector_event.started_at,
            resolved_at=connector_event.resolved_at,
            duration=connector_event.duration,
            raw_payload=connector_event.raw_payload,
        )

    @staticmethod
    def _apply_connector_event(event: Event, connector_event: ConnectorEvent) -> None:
        event.host = connector_event.host
        event.severity = connector_event.severity
        event.status = connector_event.status
        event.problem_name = connector_event.problem_name
        event.started_at = connector_event.started_at
        event.resolved_at = connector_event.resolved_at
        event.duration = connector_event.duration
        event.raw_payload = connector_event.raw_payload
