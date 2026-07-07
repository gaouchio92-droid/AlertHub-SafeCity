"""Report query services."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.sql.elements import ColumnElement

from app.models.event import Event
from app.schemas.reports import (
    WeeklyDiscordReportDataQualityResponse,
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
        base_filters: tuple[ColumnElement[bool], ...] = (
            Event.source == "discord",
            Event.started_at >= period_start,
            Event.started_at <= period_end,
            Event.problem_name.is_not(None),
        )

        total_events = self._db.scalar(
            select(func.count()).select_from(Event).where(*base_filters)
        ) or 0
        resolved_events = self._db.scalar(
            select(func.count())
            .select_from(Event)
            .where(*base_filters, Event.resolved_at.is_not(None))
        ) or 0
        unnamed_events = self._count_missing(Event.problem_name, base_filters)
        unknown_severity_events = self._count_missing(Event.severity, base_filters)
        unknown_host_events = self._count_missing(Event.host, base_filters)

        return WeeklyDiscordReportResponse(
            source="discord",
            period_start=period_start,
            period_end=period_end,
            total_events=total_events,
            open_events=max(total_events - resolved_events, 0),
            resolved_events=resolved_events,
            data_quality=self._data_quality(
                unnamed_events=unnamed_events,
                unknown_severity_events=unknown_severity_events,
                unknown_host_events=unknown_host_events,
            ),
            by_severity=self._metrics("severity", base_filters),
            by_host=self._metrics("host", base_filters),
            recent_events=self._recent_events(base_filters),
        )

    def _metrics(
        self,
        field_name: str,
        base_filters: tuple[ColumnElement[bool], ...],
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
            WeeklyDiscordReportMetricResponse(label=self._display_label(label), value=count)
            for label, count in rows
        ]

    def _recent_events(
        self,
        base_filters: tuple[ColumnElement[bool], ...],
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
                title=self._event_title(event),
                host=event.host,
                severity=event.severity,
                status=event.status,
                problem_name=event.problem_name,
                started_at=event.started_at,
                details_available=bool(event.problem_name or event.severity),
                operational_data=self._normalized_value(event, "operational_data"),
                links=self._normalized_links(event),
            )
            for event in events
        ]

    def _count_missing(
        self,
        column: ColumnElement[str | None] | InstrumentedAttribute[str | None],
        base_filters: tuple[ColumnElement[bool], ...],
    ) -> int:
        return self._db.scalar(
            select(func.count())
            .select_from(Event)
            .where(*base_filters, column.is_(None))
        ) or 0

    @staticmethod
    def _data_quality(
        *,
        unnamed_events: int,
        unknown_severity_events: int,
        unknown_host_events: int,
    ) -> WeeklyDiscordReportDataQualityResponse:
        warnings: list[str] = []
        if unnamed_events:
            warnings.append(
                "Discord returned messages without readable content or embeds. Enable Message "
                "Content Intent for the bot, then sync again."
            )
        if unknown_severity_events:
            warnings.append(
                "Severity is unknown until the Zabbix Discord message format is parsed."
            )
        if unknown_host_events:
            warnings.append("Some events do not include a detectable host.")
        return WeeklyDiscordReportDataQualityResponse(
            unnamed_events=unnamed_events,
            unknown_severity_events=unknown_severity_events,
            unknown_host_events=unknown_host_events,
            warnings=warnings,
        )

    @staticmethod
    def _display_label(value: object) -> str:
        if value is None or str(value).strip() == "":
            return "Not detected yet"
        return str(value)

    @staticmethod
    def _event_title(event: Event) -> str:
        if event.problem_name:
            return event.problem_name
        if event.problem_id:
            return f"Discord message {event.problem_id[-6:]}"
        return "Discord message without readable details"

    @staticmethod
    def _normalized_value(event: Event, key: str) -> str | None:
        normalized = event.raw_payload.get("normalized")
        if not isinstance(normalized, dict):
            return None
        value = normalized.get(key)
        return str(value) if value else None

    @staticmethod
    def _normalized_links(event: Event) -> list[str]:
        normalized = event.raw_payload.get("normalized")
        if not isinstance(normalized, dict):
            return []
        links = normalized.get("links")
        if not isinstance(links, list):
            return []
        return [str(link) for link in links if link]
