"""Event query services."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.orm import Session

from app.connectors.base import ConnectorEvent
from app.core.config.settings import get_settings
from app.models.event import Event

OPEN_STATUSES = {"problem", "open", "active"}
SEVERITY_PRIORITY = {
    "disaster": 100,
    "high": 90,
    "average": 70,
    "warning": 50,
    "information": 25,
    "not_classified": 10,
}
SEVERITY_SLA = {
    "disaster": timedelta(minutes=30),
    "high": timedelta(hours=1),
    "average": timedelta(hours=4),
    "warning": timedelta(hours=12),
    "information": timedelta(days=2),
    "not_classified": timedelta(days=3),
}


class EventIngestionResult:
    """Event ingestion counters."""

    def __init__(self, *, received: int, created: int, updated: int) -> None:
        self.received = received
        self.created = created
        self.updated = updated


@dataclass(frozen=True)
class EventSummaryMetric:
    """Count grouped by one event attribute."""

    label: str
    value: int


@dataclass(frozen=True)
class EventSummary:
    """Operational event summary."""

    total_events: int
    open_events: int
    resolved_events: int
    unparsed_events: int
    last_event_at: datetime | None
    by_source: list[EventSummaryMetric]
    by_status: list[EventSummaryMetric]
    by_severity: list[EventSummaryMetric]


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

    def summarize_events(self) -> EventSummary:
        """Return aggregated event counters for operational dashboards."""
        total_events = self._count_events()
        open_events = self._count_events(Event.status.in_(("problem", "open", "active")))
        resolved_events = self._count_events(Event.status == "resolved")
        unparsed_events = self._count_events(Event.problem_name.is_(None))
        last_event_at = self._db.scalar(
            select(Event.started_at)
            .where(Event.started_at.is_not(None))
            .order_by(Event.started_at.desc())
            .limit(1)
        )

        return EventSummary(
            total_events=total_events,
            open_events=open_events,
            resolved_events=resolved_events,
            unparsed_events=unparsed_events,
            last_event_at=last_event_at,
            by_source=self._count_by(Event.source),
            by_status=self._count_by(Event.status),
            by_severity=self._count_by(Event.severity),
        )

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

    def _count_events(self, *conditions: Any) -> int:
        statement = select(func.count(Event.id))
        for condition in conditions:
            statement = statement.where(condition)
        return self._db.scalar(statement) or 0

    def _count_by(self, column: Any) -> list[EventSummaryMetric]:
        rows = self._db.execute(
            select(column, func.count(Event.id))
            .group_by(column)
            .order_by(func.count(Event.id).desc())
            .limit(8)
        ).all()
        return [
            EventSummaryMetric(
                label=str(label) if label else "unknown",
                value=count,
            )
            for label, count in rows
        ]

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
                "raw_payload": EventService._merge_raw_payloads(
                    current_event.raw_payload,
                    next_event.raw_payload,
                ),
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
        normalized = EventService._normalized_payload(connector_event)
        escalation = EventService._escalation_context(connector_event)
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
            operational_data=EventService._normalized_string(normalized, "operational_data"),
            links=EventService._normalized_links(normalized),
            escalation_priority=escalation["priority"],
            escalation_level=escalation["level"],
            escalation_owner=escalation["owner"],
            escalation_due_at=escalation["due_at"],
            raw_payload=connector_event.raw_payload,
        )

    @staticmethod
    def _apply_connector_event(event: Event, connector_event: ConnectorEvent) -> None:
        normalized = EventService._normalized_payload(connector_event)
        escalation = EventService._escalation_context(connector_event)
        event.host = connector_event.host
        event.severity = connector_event.severity
        event.status = connector_event.status
        event.problem_name = connector_event.problem_name
        event.started_at = connector_event.started_at
        event.resolved_at = connector_event.resolved_at
        event.duration = connector_event.duration
        event.operational_data = EventService._normalized_string(normalized, "operational_data")
        event.links = EventService._normalized_links(normalized)
        event.escalation_priority = escalation["priority"]
        event.escalation_level = escalation["level"]
        event.escalation_owner = escalation["owner"]
        event.escalation_due_at = escalation["due_at"]
        event.raw_payload = connector_event.raw_payload

    @staticmethod
    def _normalized_payload(connector_event: ConnectorEvent) -> dict[str, Any]:
        normalized = connector_event.raw_payload.get("normalized")
        return normalized if isinstance(normalized, dict) else {}

    @staticmethod
    def _merge_raw_payloads(
        current_payload: dict[str, Any],
        next_payload: dict[str, Any],
    ) -> dict[str, Any]:
        merged = {**current_payload, **next_payload}
        current_normalized = current_payload.get("normalized")
        next_normalized = next_payload.get("normalized")
        if isinstance(current_normalized, dict) or isinstance(next_normalized, dict):
            merged_normalized = {
                **(current_normalized if isinstance(current_normalized, dict) else {}),
                **(next_normalized if isinstance(next_normalized, dict) else {}),
            }
            current_links = current_normalized.get("links") if isinstance(current_normalized, dict) else []
            next_links = next_normalized.get("links") if isinstance(next_normalized, dict) else []
            current_links = current_links if isinstance(current_links, list) else []
            next_links = next_links if isinstance(next_links, list) else []
            links = [str(link) for link in [*current_links, *next_links] if link]
            merged_normalized["links"] = list(dict.fromkeys(links))
            if not merged_normalized.get("operational_data") and isinstance(current_normalized, dict):
                merged_normalized["operational_data"] = current_normalized.get("operational_data")
            merged["normalized"] = merged_normalized
        return merged

    @staticmethod
    def _normalized_string(normalized: dict[str, Any], key: str) -> str | None:
        value = normalized.get(key)
        return str(value) if value else None

    @staticmethod
    def _normalized_links(normalized: dict[str, Any]) -> list[str]:
        links = normalized.get("links")
        if not isinstance(links, list):
            return []
        return [str(link) for link in links if link]

    @staticmethod
    def _escalation_context(connector_event: ConnectorEvent) -> dict[str, Any]:
        severity = (connector_event.severity or "not_classified").lower()
        status = (connector_event.status or "").lower()
        if status not in OPEN_STATUSES:
            return {
                "priority": None,
                "level": None,
                "owner": None,
                "due_at": None,
            }

        now = datetime.now(UTC)
        started_at = EventService._aware_datetime(connector_event.started_at) or now
        age_seconds = max(int((now - started_at).total_seconds()), 0)
        base_priority = SEVERITY_PRIORITY.get(severity, SEVERITY_PRIORITY["not_classified"])
        age_boost = min(age_seconds // 3600, 30)
        priority = min(base_priority + age_boost, 100)

        if priority >= 95:
            level = "P1"
        elif priority >= 75:
            level = "P2"
        elif priority >= 50:
            level = "P3"
        else:
            level = "P4"

        sla = SEVERITY_SLA.get(severity, SEVERITY_SLA["not_classified"])
        return {
            "priority": priority,
            "level": level,
            "owner": EventService._owner_for_severity(severity),
            "due_at": started_at + sla,
        }

    @staticmethod
    def _owner_for_severity(severity: str) -> str:
        settings = get_settings()
        rules: dict[str, str] = {}
        for item in settings.escalation_owner_rules.split(";"):
            if ":" not in item:
                continue
            key, value = item.split(":", 1)
            rules[key.strip().lower()] = value.strip()
        return rules.get(severity, settings.default_escalation_owner)

    @staticmethod
    def _aware_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
