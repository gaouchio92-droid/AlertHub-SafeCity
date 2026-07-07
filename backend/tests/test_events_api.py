"""Event API endpoint tests."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.endpoints import events as events_endpoint
from app.connectors.base import ConnectorEvent
from app.main import app
from app.schemas.events import EventResponse
from app.services.events import EventIngestionResult, EventSummary, EventSummaryMetric


class StubEventService:
    """Test double for event queries."""

    last_limit: int | None = None
    last_offset: int | None = None
    last_source: str | None = None
    last_status: str | None = None
    last_severity: str | None = None
    last_query: str | None = None
    last_include_unparsed: bool | None = None

    def __init__(self, db: object) -> None:
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
    ) -> tuple[list[EventResponse], int]:
        """Return deterministic API test data."""
        StubEventService.last_limit = limit
        StubEventService.last_offset = offset
        StubEventService.last_source = source
        StubEventService.last_status = status
        StubEventService.last_severity = severity
        StubEventService.last_query = query
        StubEventService.last_include_unparsed = include_unparsed
        timestamp = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
        return [
            EventResponse(
                id=uuid4(),
                source=source or "discord",
                problem_id="discord-message-1",
                host="router-01",
                severity=severity or "high",
                status=status or "problem",
                problem_name="Interface down",
                started_at=timestamp,
                resolved_at=None,
                duration=None,
                raw_payload={"content": "Interface down"},
                created_at=timestamp,
                updated_at=timestamp,
            )
        ], 1

    def summarize_events(self) -> EventSummary:
        """Return deterministic summary data."""
        timestamp = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
        return EventSummary(
            total_events=10,
            open_events=3,
            resolved_events=7,
            unparsed_events=1,
            last_event_at=timestamp,
            by_source=[EventSummaryMetric(label="discord", value=10)],
            by_status=[
                EventSummaryMetric(label="resolved", value=7),
                EventSummaryMetric(label="problem", value=3),
            ],
            by_severity=[EventSummaryMetric(label="high", value=4)],
        )


class StubSyncEventService:
    """Test double for event ingestion."""

    received_events: list[ConnectorEvent] = []

    def __init__(self, db: object) -> None:
        self._db = db

    def upsert_connector_events(
        self,
        connector_events: list[ConnectorEvent],
    ) -> EventIngestionResult:
        """Capture connector events and return deterministic counters."""
        self.received_events = connector_events
        return EventIngestionResult(received=len(connector_events), created=1, updated=1)


class StubConnectorManager:
    """Test double for connector synchronization."""

    async def sync(self) -> list[ConnectorEvent]:
        """Return deterministic connector events."""
        return [
            ConnectorEvent(
                source="discord",
                problem_id="message-1",
                status="received",
                raw_payload={"content": "first"},
            ),
            ConnectorEvent(
                source="discord",
                problem_id="message-2",
                status="received",
                raw_payload={"content": "second"},
            ),
        ]


def test_list_events_returns_paginated_events(monkeypatch: object) -> None:
    monkeypatch.setattr(events_endpoint, "EventService", StubEventService)
    client = TestClient(app)

    response = client.get(
        "/api/v1/events",
        params={
            "limit": 10,
            "offset": 5,
            "source": "discord",
            "status": "problem",
            "severity": "high",
            "q": "router",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["limit"] == 10
    assert payload["offset"] == 5
    assert payload["items"][0]["source"] == "discord"
    assert payload["items"][0]["raw_payload"] == {"content": "Interface down"}
    assert StubEventService.last_limit == 10
    assert StubEventService.last_offset == 5
    assert StubEventService.last_source == "discord"
    assert StubEventService.last_status == "problem"
    assert StubEventService.last_severity == "high"
    assert StubEventService.last_query == "router"
    assert StubEventService.last_include_unparsed is False


def test_event_summary_returns_operational_counters(monkeypatch: object) -> None:
    monkeypatch.setattr(events_endpoint, "EventService", StubEventService)
    client = TestClient(app)

    response = client.get("/api/v1/events/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_events"] == 10
    assert payload["open_events"] == 3
    assert payload["resolved_events"] == 7
    assert payload["unparsed_events"] == 1
    assert payload["by_source"] == [{"label": "discord", "value": 10}]


def test_list_events_can_include_unparsed_events(monkeypatch: object) -> None:
    monkeypatch.setattr(events_endpoint, "EventService", StubEventService)
    client = TestClient(app)

    response = client.get("/api/v1/events", params={"include_unparsed": "true"})

    assert response.status_code == 200
    assert StubEventService.last_include_unparsed is True


def test_list_events_validates_limit() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/events", params={"limit": 101})

    assert response.status_code == 422


def test_sync_events_collects_and_persists_connector_events(monkeypatch: object) -> None:
    monkeypatch.setattr(events_endpoint, "connector_manager", StubConnectorManager())
    monkeypatch.setattr(events_endpoint, "EventService", StubSyncEventService)
    client = TestClient(app)

    response = client.post("/api/v1/events/sync")

    assert response.status_code == 200
    assert response.json() == {"received": 2, "created": 1, "updated": 1}
