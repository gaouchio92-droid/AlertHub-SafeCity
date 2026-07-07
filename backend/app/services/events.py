"""Event query services."""

from sqlalchemy import Select, delete, func, or_, select
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
        query: str | None = None,
        include_unparsed: bool = False,
    ) -> tuple[list[Event], int]:
        """Return paginated events ordered by newest first."""
        statement = self._base_query(
            source=source,
            status=status,
            severity=severity,
            query=query,
            include_unparsed=include_unparsed,
        )
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
        unique_events = self._deduplicate_connector_events(connector_events)

        for connector_event in unique_events:
            event = self._find_existing_event(connector_event)
            if event is None:
                self._db.add(self._build_event(connector_event))
                created += 1
                continue

            self._apply_connector_event(event, connector_event)
            updated += 1

        self._delete_superseded_placeholder_events(connector_events)
        self._db.commit()
        return EventIngestionResult(
            received=len(connector_events),
            created=created,
            updated=updated,
        )

    @classmethod
    def _deduplicate_connector_events(
        cls,
        connector_events: list[ConnectorEvent],
    ) -> list[ConnectorEvent]:
        """Collapse duplicate source/problem pairs before database upsert."""
        unique_events: dict[tuple[str, str], ConnectorEvent] = {}
        events_without_problem_id: list[ConnectorEvent] = []

        for connector_event in connector_events:
            if not connector_event.problem_id:
                events_without_problem_id.append(connector_event)
                continue

            key = (connector_event.source, connector_event.problem_id)
            existing_event = unique_events.get(key)
            if existing_event is None:
                unique_events[key] = connector_event
                continue
            unique_events[key] = cls._merge_connector_events(
                existing_event,
                connector_event,
            )

        return [*unique_events.values(), *events_without_problem_id]

    @staticmethod
    def _merge_connector_events(
        current_event: ConnectorEvent,
        next_event: ConnectorEvent,
    ) -> ConnectorEvent:
        """Merge repeated connector events that represent the same source problem."""
        status = next_event.status or current_event.status
        if current_event.status == "resolved" or next_event.status == "resolved":
            status = "resolved"

        started_at_values = [
            value
            for value in (current_event.started_at, next_event.started_at)
            if value is not None
        ]
        resolved_at_values = [
            value
            for value in (current_event.resolved_at, next_event.resolved_at)
            if value is not None
        ]

        return current_event.model_copy(
            update={
                "host": next_event.host or current_event.host,
                "severity": next_event.severity or current_event.severity,
                "status": status,
                "problem_name": next_event.problem_name or current_event.problem_name,
                "started_at": min(started_at_values) if started_at_values else None,
                "resolved_at": max(resolved_at_values) if resolved_at_values else None,
                "duration": next_event.duration or current_event.duration,
                "raw_payload": next_event.raw_payload or current_event.raw_payload,
            }
        )

    def _delete_superseded_placeholder_events(
        self,
        connector_events: list[ConnectorEvent],
    ) -> None:
        """Remove old unreadable Discord placeholders once parsed events exist."""
        message_ids_by_source: dict[str, set[str]] = {}
        for connector_event in connector_events:
            discord_message_id = self._normalized_discord_message_id(connector_event)
            if discord_message_id:
                message_ids_by_source.setdefault(connector_event.source, set()).add(
                    discord_message_id
                )

        for source, message_ids in message_ids_by_source.items():
            self._db.execute(
                delete(Event).where(
                    Event.source == source,
                    Event.problem_id.in_(message_ids),
                    Event.problem_name.is_(None),
                )
            )

    @staticmethod
    def _normalized_discord_message_id(connector_event: ConnectorEvent) -> str | None:
        normalized = connector_event.raw_payload.get("normalized")
        if not isinstance(normalized, dict):
            return None
        message_id = normalized.get("discord_message_id")
        return str(message_id) if message_id else None

    @staticmethod
    def _base_query(
        *,
        source: str | None,
        status: str | None,
        severity: str | None,
        query: str | None,
        include_unparsed: bool,
    ) -> Select[tuple[Event]]:
        statement = select(Event)
        if source:
            statement = statement.where(Event.source == source)
        if status:
            statement = statement.where(Event.status == status)
        if severity:
            statement = statement.where(Event.severity == severity)
        if query:
            search = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    Event.problem_id.ilike(search),
                    Event.host.ilike(search),
                    Event.severity.ilike(search),
                    Event.status.ilike(search),
                    Event.problem_name.ilike(search),
                )
            )
        if not include_unparsed:
            statement = statement.where(Event.problem_name.is_not(None))
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
