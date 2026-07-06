"""Event API endpoint tests."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.v1.endpoints import events as events_endpoint
from app.main import app
from app.schemas.events import EventResponse


class StubEventService:
    """Test double for event queries."""

    last_limit: int | None = None
    last_offset: int | None = None
    last_source: str | None = None
    last_status: str | None = None
    last_severity: str | None = None

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
    ) -> tuple[list[EventResponse], int]:
        """Return deterministic API test data."""
        StubEventService.last_limit = limit
        StubEventService.last_offset = offset
        StubEventService.last_source = source
        StubEventService.last_status = status
        StubEventService.last_severity = severity
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


def test_list_events_validates_limit() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/events", params={"limit": 101})

    assert response.status_code == 422
