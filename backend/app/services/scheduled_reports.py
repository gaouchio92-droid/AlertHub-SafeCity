"""Automatic Discord report delivery service."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config.settings import Settings
from app.models.report_delivery import ScheduledReportDelivery
from app.services.discord_report_publisher import (
    DiscordReportPublisher,
    DiscordReportPublisherError,
)
from app.services.reports import ReportService


class ScheduledReportService:
    """Publish due management reports to Discord and track delivery attempts."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    def publish_due_reports(self) -> list[ScheduledReportDelivery]:
        """Publish weekly and monthly reports when their intervals are due."""
        if not self._settings.enable_scheduled_report_delivery:
            return []

        deliveries: list[ScheduledReportDelivery] = []
        for report_kind, interval_days in (
            ("weekly", self._settings.weekly_report_interval_days),
            ("monthly", self._settings.monthly_report_interval_days),
        ):
            if self._is_due(report_kind, interval_days):
                deliveries.append(self._publish_report(report_kind))

        self._db.commit()
        return deliveries

    def _is_due(self, report_kind: str, interval_days: int) -> bool:
        latest_attempt = self._db.scalar(
            select(ScheduledReportDelivery.sent_at)
            .where(ScheduledReportDelivery.report_kind == report_kind)
            .order_by(ScheduledReportDelivery.sent_at.desc())
            .limit(1)
        )
        if latest_attempt and datetime.now(UTC) - latest_attempt < timedelta(days=1):
            return False

        latest_success = self._db.scalar(
            select(ScheduledReportDelivery.sent_at)
            .where(
                ScheduledReportDelivery.report_kind == report_kind,
                ScheduledReportDelivery.status == "delivered",
            )
            .order_by(ScheduledReportDelivery.sent_at.desc())
            .limit(1)
        )
        if latest_success is None:
            return True
        return datetime.now(UTC) - latest_success >= timedelta(days=interval_days)

    def _publish_report(self, report_kind: str) -> ScheduledReportDelivery:
        filename = f"alerthub-{report_kind}-discord-report.pdf"
        report_service = ReportService(self._db)
        if report_kind == "monthly":
            content = report_service.build_monthly_discord_management_pdf()
            summary = (
                "**AlertHub Safe City**\n"
                "Rapport mensuel automatique genere sur 4 semaines. "
                "Veuillez consulter le PDF joint pour la synthese et les escalades."
            )
        else:
            content = report_service.build_weekly_discord_management_pdf()
            summary = (
                "**AlertHub Safe City**\n"
                "Rapport hebdomadaire automatique genere sur 7 jours. "
                "Veuillez consulter le PDF joint pour les problemes non resolus."
            )

        try:
            delivery = DiscordReportPublisher(self._settings).publish_pdf(
                content,
                filename=filename,
                summary=summary,
            )
            record = ScheduledReportDelivery(
                report_kind=report_kind,
                channel_id=delivery.channel_id,
                message_id=delivery.message_id,
                filename=delivery.filename,
                status="delivered",
            )
        except DiscordReportPublisherError as exc:
            record = ScheduledReportDelivery(
                report_kind=report_kind,
                channel_id=self._settings.discord_channel_id or "unconfigured",
                message_id=None,
                filename=filename,
                status="failed",
                error_message=str(exc),
            )

        self._db.add(record)
        return record
