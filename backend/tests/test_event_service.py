"""Event service ingestion behavior tests."""

from datetime import UTC, datetime, timedelta

from app.connectors.base import ConnectorEvent
from app.services.events import EventService


def test_deduplicate_connector_events_merges_repeated_problem_updates() -> None:
    """Repeated source problem updates are merged before database insertion."""
    started_at = datetime(2026, 7, 6, 22, 20, tzinfo=UTC)
    resolved_at = started_at + timedelta(minutes=15)

    events = EventService._deduplicate_connector_events(
        [
            ConnectorEvent(
                source="discord",
                problem_id="51548",
                host="MSPC-DCAGG-SW1",
                severity="Warning",
                status="problem",
                problem_name="High bandwidth usage",
                started_at=started_at,
                raw_payload={"message": "problem"},
            ),
            ConnectorEvent(
                source="discord",
                problem_id="51548",
                host="MSPC-DCAGG-SW1",
                severity="Warning",
                status="resolved",
                problem_name="High bandwidth usage",
                started_at=started_at + timedelta(seconds=1),
                resolved_at=resolved_at,
                duration=900,
                raw_payload={"message": "resolved"},
            ),
        ]
    )

    assert len(events) == 1
    assert events[0].problem_id == "51548"
    assert events[0].status == "resolved"
    assert events[0].started_at == started_at
    assert events[0].resolved_at == resolved_at
    assert events[0].duration == 900
    assert events[0].raw_payload == {"message": "resolved"}


def test_normalized_discord_message_id_returns_message_id() -> None:
    """Discord message IDs from normalized payloads can supersede placeholders."""
    event = ConnectorEvent(
        source="discord",
        problem_id="51548",
        status="resolved",
        raw_payload={"normalized": {"discord_message_id": "1524089260699943118"}},
    )

    assert (
        EventService._normalized_discord_message_id(event)
        == "1524089260699943118"
    )
