"""Report status endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.reports import WeeklyDiscordReportResponse, WeeklyDiscordReportStatusResponse
from app.services.reports import ReportService

router = APIRouter()


@router.get(
    "/weekly-discord/status",
    response_model=WeeklyDiscordReportStatusResponse,
    summary="Weekly Discord report status",
)
async def weekly_discord_report_status() -> WeeklyDiscordReportStatusResponse:
    """Return the current implementation status for weekly Discord reports."""
    return WeeklyDiscordReportStatusResponse(
        feature="Weekly Discord report",
        implemented=True,
        visible_in_ui=True,
        reason=(
            "Discord ingestion and normalized event persistence are active. The report is "
            "generated from events stored during the last seven days."
        ),
        required_before_available=[
            "Keep DISCORD_TOKEN and DISCORD_CHANNEL_ID configured",
            "Run connector synchronization to refresh events",
            "Improve source-specific parsing as message formats are identified",
        ],
    )


@router.get(
    "/weekly-discord",
    response_model=WeeklyDiscordReportResponse,
    summary="Weekly Discord report",
)
def weekly_discord_report(
    db: Annotated[Session, Depends(get_db)],
) -> WeeklyDiscordReportResponse:
    """Return a rolling seven-day Discord report."""
    return ReportService(db).build_weekly_discord_report()
