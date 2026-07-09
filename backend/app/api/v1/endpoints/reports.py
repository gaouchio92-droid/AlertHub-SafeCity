"""Report status endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config.settings import Settings, get_settings
from app.database.session import get_db
from app.schemas.reports import (
    WeeklyDiscordReportPushResponse,
    WeeklyDiscordReportResponse,
    WeeklyDiscordReportStatusResponse,
)
from app.services.discord_report_publisher import (
    DiscordReportPublisher,
    DiscordReportPublisherError,
)
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


@router.get(
    "/weekly-discord/export",
    response_class=Response,
    summary="Export weekly Discord management report",
)
def export_weekly_discord_report(
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Return a Markdown report suitable for management sharing."""
    content = ReportService(db).build_weekly_discord_management_report()
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="alerthub-weekly-discord-report.md"'
            ),
        },
    )


@router.get(
    "/weekly-discord/export.pdf",
    response_class=Response,
    summary="Export weekly Discord management report as PDF",
)
def export_weekly_discord_report_pdf(
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Return a polished PDF report suitable for management sharing."""
    content = ReportService(db).build_weekly_discord_management_pdf()
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                'attachment; filename="alerthub-weekly-discord-report.pdf"'
            ),
        },
    )


@router.post(
    "/weekly-discord/push-discord",
    response_model=WeeklyDiscordReportPushResponse,
    summary="Push weekly Discord PDF report to Discord",
)
def push_weekly_discord_report_to_discord(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> WeeklyDiscordReportPushResponse:
    """Generate the weekly PDF report and publish it to the configured Discord channel."""
    filename = "alerthub-weekly-discord-report.pdf"
    content = ReportService(db).build_weekly_discord_management_pdf()
    try:
        delivery = DiscordReportPublisher(settings).publish_pdf(
            content,
            filename=filename,
            summary=(
                "**AlertHub Safe City**\n"
                "Rapport hebdomadaire PDF genere automatiquement. "
                "Veuillez consulter la piece jointe pour les problemes non resolus."
            ),
        )
    except DiscordReportPublisherError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return WeeklyDiscordReportPushResponse(
        delivered=delivery.delivered,
        channel_id=delivery.channel_id,
        message_id=delivery.message_id,
        filename=delivery.filename,
    )
