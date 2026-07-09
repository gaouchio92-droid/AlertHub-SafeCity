"""Report query services."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.orm import InstrumentedAttribute, Session
from sqlalchemy.sql.elements import ColumnElement

from app.models.event import Event
from app.schemas.reports import (
    WeeklyDiscordOpenProblemResponse,
    WeeklyDiscordReportDailyTrendResponse,
    WeeklyDiscordReportDataQualityResponse,
    WeeklyDiscordReportEventResponse,
    WeeklyDiscordReportMetricResponse,
    WeeklyDiscordReportResponse,
    WeeklyDiscordSecurityAdvisoryResponse,
)
from app.services.report_pdf import build_weekly_discord_pdf


class ReportService:
    """Build report payloads from normalized events."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def build_weekly_discord_report(self) -> WeeklyDiscordReportResponse:
        """Return a rolling seven-day Discord event report."""
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=7)
        all_discord_filters: tuple[ColumnElement[bool], ...] = (
            Event.source == "discord",
            Event.started_at >= period_start,
            Event.started_at <= period_end,
        )
        readable_filters: tuple[ColumnElement[bool], ...] = (
            *all_discord_filters,
            Event.problem_name.is_not(None),
        )

        total_events = self._db.scalar(
            select(func.count()).select_from(Event).where(*all_discord_filters)
        ) or 0
        resolved_events = self._db.scalar(
            select(func.count())
            .select_from(Event)
            .where(*readable_filters, Event.resolved_at.is_not(None))
        ) or 0
        open_problem_filters: tuple[ColumnElement[bool], ...] = (
            *readable_filters,
            Event.resolved_at.is_(None),
            Event.status != "resolved",
        )
        open_events = self._db.scalar(
            select(func.count()).select_from(Event).where(*open_problem_filters)
        ) or 0
        unnamed_events = self._count_missing(Event.problem_name, all_discord_filters)
        unknown_severity_events = self._count_missing(Event.severity, all_discord_filters)
        unknown_host_events = self._count_missing(Event.host, all_discord_filters)

        return WeeklyDiscordReportResponse(
            source="discord",
            period_start=period_start,
            period_end=period_end,
            total_events=total_events,
            open_events=open_events,
            resolved_events=resolved_events,
            data_quality=self._data_quality(
                unnamed_events=unnamed_events,
                unknown_severity_events=unknown_severity_events,
                unknown_host_events=unknown_host_events,
            ),
            by_severity=self._metrics("severity", readable_filters),
            by_host=self._metrics("host", readable_filters),
            daily_trend=self._daily_trend(
                period_start.date(),
                period_end.date(),
                all_discord_filters,
            ),
            security_advisories=self._security_advisories(),
            open_problems=self._open_problems(open_problem_filters, period_end),
            recent_events=self._recent_events(readable_filters),
        )

    def build_weekly_discord_management_report(self) -> str:
        """Return a Markdown report suitable for operational management."""
        report = self.build_weekly_discord_report()
        readable_events = max(report.total_events - report.data_quality.unnamed_events, 0)
        lines = [
            "# Rapport hebdomadaire AlertHub Safe City",
            "",
            "## Synthese executive",
            "",
            (
                f"Periode analysee: {report.period_start:%Y-%m-%d %H:%M UTC} "
                f"au {report.period_end:%Y-%m-%d %H:%M UTC}."
            ),
            f"Source principale: {report.source}.",
            f"Messages Discord analyses: {report.total_events}.",
            f"Alertes lisibles: {readable_events}.",
            f"Problemes encore ouverts: {report.open_events}.",
            f"Problemes resolus: {report.resolved_events}.",
            "",
            "## Points de vigilance",
            "",
            *self._management_findings(report),
            "",
            "## Top equipements concernes",
            "",
            *self._metric_lines(report.by_host),
            "",
            "## Repartition par severite",
            "",
            *self._metric_lines(report.by_severity),
            "",
            "## Derniers evenements significatifs",
            "",
            *self._event_lines(report),
            "",
            "## Problemes non resolus",
            "",
            *self._open_problem_lines(report),
            "",
            "## Veille securite applicative",
            "",
            *self._security_advisory_lines(report),
            "",
            "## Recommandations de stabilisation",
            "",
            *self._stabilization_recommendations(report),
            "",
            "## Prochaines actions conseillees",
            "",
            "- Planifier une revue quotidienne des problemes ouverts.",
            "- Confirmer que le bot Discord a acces au bon salon d'alertes.",
            "- Standardiser le format des messages Discord emis par la supervision.",
            "- Surveiller les erreurs backend et la sante Docker Compose apres chaque deploiement.",
            "",
            "_Rapport genere automatiquement par AlertHub Safe City._",
            "",
        ]
        return "\n".join(lines)

    def build_weekly_discord_management_pdf(self) -> bytes:
        """Return a polished PDF report suitable for operational management."""
        report = self.build_weekly_discord_report()
        return build_weekly_discord_pdf(
            report,
            findings=self._management_findings(report),
            recommendations=self._stabilization_recommendations(report),
        )

    @staticmethod
    def _security_advisories() -> list[WeeklyDiscordSecurityAdvisoryResponse]:
        """Return current security watch items for the AlertHub runtime stack."""
        return [
            WeeklyDiscordSecurityAdvisoryResponse(
                component="Vite dev server",
                current_version="6.0.5",
                severity="High",
                status="Upgrade required",
                finding=(
                    "Recent Vite advisories affect 6.x dev-server file access controls before "
                    "6.4.2. Production builds are less exposed, but development servers must not "
                    "be internet-facing."
                ),
                recommendation=(
                    "Upgrade Vite to at least 6.4.2, keep the dev server local-only, and never "
                    "expose .env or source maps from development environments."
                ),
                reference="NVD CVE-2026-39365 / Vite advisories",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="Nginx reverse proxy",
                current_version="1.27-alpine",
                severity="High",
                status="Upgrade required",
                finding=(
                    "The configured Nginx image is behind current fixed branches listed in 2026 "
                    "Nginx security advisories."
                ),
                recommendation=(
                    "Move to a patched stable image such as nginx:1.30.3-alpine or newer, pin "
                    "images by digest in production, and rebuild the stack."
                ),
                reference="nginx.org security advisories",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="PostgreSQL",
                current_version="16-alpine",
                severity="Medium",
                status="Patch validation required",
                finding=(
                    "The major tag does not show the exact minor version in configuration. "
                    "PostgreSQL security fixes are delivered through minor releases."
                ),
                recommendation=(
                    "Pin and run the latest PostgreSQL 16 minor image, verify backups before "
                    "upgrade, then apply migrations after the database is healthy."
                ),
                reference="PostgreSQL security information",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="FastAPI / Starlette stack",
                current_version="FastAPI 0.115.14",
                severity="Medium",
                status="Monitor and audit",
                finding=(
                    "FastAPI depends on Starlette and ASGI middleware behavior. Recent Host "
                    "header and request handling advisories make dependency auditing important."
                ),
                recommendation=(
                    "Run pip-audit in CI, pin Starlette through FastAPI-compatible upgrades, "
                    "and keep trusted host/proxy headers strict at the edge."
                ),
                reference="FastAPI and Starlette advisories",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="Secrets and Discord token",
                current_version="Environment-based secrets",
                severity="High",
                status="Operational control required",
                finding=(
                    "Discord tokens, database credentials, and JWT secrets are environment "
                    "secrets. Exposure would allow bot abuse or data access."
                ),
                recommendation=(
                    "Rotate exposed tokens immediately, keep .env out of Git, use production "
                    "secret storage, and restrict bot permissions to the reporting channel."
                ),
                reference="AlertHub security baseline",
            ),
        ]

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

    def _daily_trend(
        self,
        period_start: date,
        period_end: date,
        base_filters: tuple[ColumnElement[bool], ...],
    ) -> list[WeeklyDiscordReportDailyTrendResponse]:
        day_column = func.date(Event.started_at)
        rows = self._db.execute(
            select(
                day_column.label("event_day"),
                func.count().label("total"),
                func.sum(case((Event.status == "problem", 1), else_=0)).label("problem"),
                func.sum(case((Event.status == "resolved", 1), else_=0)).label("resolved"),
            )
            .where(*base_filters)
            .group_by(day_column)
            .order_by(day_column)
        ).all()
        row_by_day = {
            self._coerce_date(row.event_day): {
                "total": int(row.total or 0),
                "problem": int(row.problem or 0),
                "resolved": int(row.resolved or 0),
            }
            for row in rows
        }

        days = (period_end - period_start).days
        return [
            WeeklyDiscordReportDailyTrendResponse(
                date=current_day,
                total=row_by_day.get(current_day, {}).get("total", 0),
                problem=row_by_day.get(current_day, {}).get("problem", 0),
                resolved=row_by_day.get(current_day, {}).get("resolved", 0),
            )
            for current_day in (
                period_start + timedelta(days=day_offset)
                for day_offset in range(days + 1)
            )
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
                operational_data=event.operational_data or self._normalized_value(event, "operational_data"),
                links=event.links or self._normalized_links(event),
            )
            for event in events
        ]

    def _open_problems(
        self,
        base_filters: tuple[ColumnElement[bool], ...],
        period_end: datetime,
    ) -> list[WeeklyDiscordOpenProblemResponse]:
        events = self._db.scalars(
            select(Event)
            .where(*base_filters)
            .order_by(
                Event.escalation_priority.desc().nullslast(),
                Event.started_at.asc().nullslast(),
                Event.created_at.asc(),
            )
            .limit(20)
        ).all()
        return [
            WeeklyDiscordOpenProblemResponse(
                problem_id=event.problem_id,
                title=self._event_title(event),
                host=event.host,
                severity=event.severity,
                status=event.status,
                started_at=event.started_at,
                age_seconds=self._age_seconds(event.started_at, period_end),
                age_label=self._age_label(event.started_at, period_end),
                escalation_priority=self._event_escalation_priority(event),
                escalation_level=event.escalation_level or self._event_escalation_level(event),
                escalation_owner=event.escalation_owner or self._event_escalation_owner(event),
                escalation_due_at=event.escalation_due_at,
                operational_data=event.operational_data or self._normalized_value(event, "operational_data"),
                links=event.links or self._normalized_links(event),
                recommended_action=self._recommended_action(event),
            )
            for event in events
        ]

    def _management_findings(
        self,
        report: WeeklyDiscordReportResponse,
    ) -> list[str]:
        findings: list[str] = []
        if report.open_events:
            findings.append(
                f"- {report.open_events} probleme(s) restent ouverts et doivent etre suivis."
            )
        if report.data_quality.unnamed_events:
            findings.append(
                "- Certains messages Discord ne sont pas encore entierement lisibles par le "
                "parseur."
            )
        if not report.total_events:
            findings.append("- Aucun evenement Discord exploitable n'a ete detecte sur la periode.")
        if not findings:
            findings.append("- Aucun point critique detecte sur la periode.")
        return findings

    def _metric_lines(
        self,
        metrics: list[WeeklyDiscordReportMetricResponse],
    ) -> list[str]:
        if not metrics:
            return ["- Aucune donnee disponible."]
        return [f"- {metric.label}: {metric.value}" for metric in metrics[:10]]

    def _event_lines(
        self,
        report: WeeklyDiscordReportResponse,
    ) -> list[str]:
        if not report.recent_events:
            return ["- Aucun evenement recent disponible."]
        return [
            (
                f"- {event.title} | host: {event.host or 'non detecte'} | "
                f"severite: {event.severity or 'non detectee'} | "
                f"statut: {event.status or 'unknown'}"
            )
            for event in report.recent_events[:8]
        ]

    def _open_problem_lines(
        self,
        report: WeeklyDiscordReportResponse,
    ) -> list[str]:
        if not report.open_problems:
            return ["- Aucun probleme non resolu detecte."]
        return [
            (
                f"- {problem.title} | host: {problem.host or 'non detecte'} | "
                f"severite: {problem.severity or 'non detectee'} | "
                f"priorite: {problem.escalation_priority or 'n/a'} | "
                f"niveau: {problem.escalation_level or 'n/a'} | "
                f"responsable: {problem.escalation_owner or 'non assigne'} | "
                f"age: {problem.age_label} | action: {problem.recommended_action}"
            )
            for problem in report.open_problems[:10]
        ]

    @staticmethod
    def _security_advisory_lines(
        report: WeeklyDiscordReportResponse,
    ) -> list[str]:
        if not report.security_advisories:
            return ["- Aucune alerte securite applicative configuree."]
        return [
            (
                f"- {item.component} ({item.current_version}) | severite: {item.severity} | "
                f"statut: {item.status} | action: {item.recommendation}"
            )
            for item in report.security_advisories
        ]

    def _stabilization_recommendations(
        self,
        report: WeeklyDiscordReportResponse,
    ) -> list[str]:
        recommendations = [
            "- Garder PostgreSQL avec volume persistant et sauvegarde planifiee.",
            "- Activer une rotation des logs backend, nginx et Docker.",
            "- Ajouter une tache de synchronisation planifiee pour eviter les imports manuels.",
            "- Mettre en place une alerte de sante sur /api/v1/health.",
            "- Executer les migrations Alembic dans le pipeline de deploiement.",
        ]
        if report.data_quality.unnamed_events or report.data_quality.unknown_host_events:
            recommendations.append(
                "- Finaliser le parsing Discord pour extraire systematiquement host, severite, "
                "statut, liens et nom du probleme."
            )
        if report.open_events:
            recommendations.append(
                "- Prioriser les problemes ouverts avec un suivi d'escalade par responsable."
            )
        return recommendations

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
    def _coerce_date(value: object) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

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

    @staticmethod
    def _age_seconds(started_at: datetime | None, period_end: datetime) -> int | None:
        if not started_at:
            return None
        return max(int((period_end - started_at).total_seconds()), 0)

    @classmethod
    def _age_label(cls, started_at: datetime | None, period_end: datetime) -> str:
        age_seconds = cls._age_seconds(started_at, period_end)
        if age_seconds is None:
            return "age inconnu"
        days, remainder = divmod(age_seconds, 86_400)
        hours, remainder = divmod(remainder, 3_600)
        minutes = remainder // 60
        if days:
            return f"{days}j {hours}h"
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @classmethod
    def _recommended_action(cls, event: Event) -> str:
        severity = (event.severity or "").lower()
        owner = event.escalation_owner or cls._event_escalation_owner(event)
        level = event.escalation_level or cls._event_escalation_level(event)
        if severity in {"disaster", "high"}:
            return f"Escalader immediatement vers {owner} ({level}) et confirmer l'impact."
        if severity == "average":
            return f"Affecter a {owner} ({level}), verifier l'equipement et suivre la resolution."
        if severity == "warning":
            return f"Surveiller avec {owner} ({level}) et confirmer si l'alerte persiste."
        return "Qualifier l'alerte et confirmer le statut terrain."

    @staticmethod
    def _event_escalation_priority(event: Event) -> int | None:
        if event.escalation_priority is not None:
            return event.escalation_priority
        severity = (event.severity or "").lower()
        fallback = {
            "disaster": 100,
            "high": 90,
            "average": 70,
            "warning": 50,
            "information": 25,
            "not_classified": 10,
        }
        return fallback.get(severity)

    @classmethod
    def _event_escalation_level(cls, event: Event) -> str:
        priority = cls._event_escalation_priority(event) or 10
        if priority >= 95:
            return "P1"
        if priority >= 75:
            return "P2"
        if priority >= 50:
            return "P3"
        return "P4"

    @staticmethod
    def _event_escalation_owner(event: Event) -> str:
        severity = (event.severity or "").lower()
        owners = {
            "disaster": "Incident Manager",
            "high": "NOC Lead",
            "average": "NOC Operator",
            "warning": "NOC Operator",
            "information": "Monitoring Team",
        }
        return owners.get(severity, "NOC Team")
