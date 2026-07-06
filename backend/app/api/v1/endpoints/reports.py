"""Report status endpoints."""

from fastapi import APIRouter

from app.schemas.reports import WeeklyDiscordReportStatusResponse

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
        implemented=False,
        visible_in_ui=True,
        reason=(
            "Sprint 1 contains platform infrastructure only. Discord ingestion, analytics, "
            "and weekly report generation are not implemented yet."
        ),
        required_before_available=[
            "Configure DISCORD_TOKEN and DISCORD_CHANNEL_ID",
            "Implement Discord message ingestion",
            "Persist normalized connector events",
            "Implement weekly aggregation and report rendering",
        ],
    )
