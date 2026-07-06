"""Report query services."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.schemas.reports import (
    WeeklyDiscordReportEventResponse,
    WeeklyDiscordReportMetricResponse,
    WeeklyDiscordReportResponse,
)


class ReportService:
    """Build report payloads from normalized events."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def build_weekly_discord_report(self) -> WeeklyDiscordReportResponse:
        """Return a rolling seven-day Discord event report."""
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=7)
        base_filters = (
            Event.source == "discord",
            Event.started_at >= period_start,
            Event.started_at <= period_end,
        )

        total_events = self._db.scalar(
            select(func.count()).select_from(Event).where(*base_filters)
        ) or 0
        resolved_events = self._db.scalar(
            select(func.count()).select_from(Event).where(*base_filters, Event.resolved_at.is_not(None))
        ) or 0

        return WeeklyDiscordReportResponse(
            source="discord",
            period_start=period_start,
            period_end=period_end,
            total_events=total_events,
            open_events=max(total_events - resolved_events, 0),
            resolved_events=resolved_events,
            by_severity=self._metrics("severity", base_filters),
            by_host=self._metrics("host", base_filters),
            recent_events=self._recent_events(base_filters),
        )

    def _metrics(
        self,
        field_name: str,
        base_filters: tuple[object, ...],
    ) -> list[WeeklyDiscordReportMetricResponse]:
        column = getattr(Event, field_name)
        rows = self._db.execute(
            select(column, func.count())
            .where(*base_filters)
            .group_by(column)
            .order_by(func.count().desc())
            .limit(10)
        ).all()
        return [
            WeeklyDiscordReportMetricResponse(label=str(label or "Unknown"), value=count)
            for label, count in rows
        ]

    def _recent_events(
        self,
        base_filters: tuple[object, ...],
    ) -> list[WeeklyDiscordReportEventResponse]:
        events = self._db.scalars(
            select(Event)
            .where(*base_filters)
            .order_by(Event.started_at.desc().nullslast(), Event.created_at.desc())
            .limit(10)
        ).all()
        return [
            WeeklyDiscordReportEventResponse(
                problem_id=event.problem_id,
                host=event.host,
                severity=event.severity,
                status=event.status,
                problem_name=event.problem_name,
                started_at=event.started_at,
            )
            for event in events
        ]
