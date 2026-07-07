"""Report API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class WeeklyDiscordReportStatusResponse(BaseModel):
    """Weekly Discord report feature status."""

    model_config = ConfigDict(frozen=True)

    feature: str
    implemented: bool
    visible_in_ui: bool
    reason: str
    required_before_available: list[str]


class WeeklyDiscordReportMetricResponse(BaseModel):
    """Named report metric."""

    model_config = ConfigDict(frozen=True)

    label: str
    value: int


class WeeklyDiscordReportEventResponse(BaseModel):
    """Compact event row for report screens."""

    model_config = ConfigDict(frozen=True)

    problem_id: str | None
    title: str
    host: str | None
    severity: str | None
    status: str | None
    problem_name: str | None
    started_at: datetime | None
    details_available: bool
    operational_data: str | None
    links: list[str]


class WeeklyDiscordReportDataQualityResponse(BaseModel):
    """Data quality counters for the weekly report."""

    model_config = ConfigDict(frozen=True)

    unnamed_events: int
    unknown_severity_events: int
    unknown_host_events: int
    warnings: list[str]


class WeeklyDiscordReportDailyTrendResponse(BaseModel):
    """Daily event trend bucket for the weekly report."""

    model_config = ConfigDict(frozen=True)

    date: date
    total: int
    problem: int
    resolved: int


class WeeklyDiscordReportResponse(BaseModel):
    """Weekly Discord report generated from normalized events."""

    model_config = ConfigDict(frozen=True)

    source: str
    period_start: datetime
    period_end: datetime
    total_events: int
    open_events: int
    resolved_events: int
    data_quality: WeeklyDiscordReportDataQualityResponse
    by_severity: list[WeeklyDiscordReportMetricResponse]
    by_host: list[WeeklyDiscordReportMetricResponse]
    daily_trend: list[WeeklyDiscordReportDailyTrendResponse]
    recent_events: list[WeeklyDiscordReportEventResponse]
