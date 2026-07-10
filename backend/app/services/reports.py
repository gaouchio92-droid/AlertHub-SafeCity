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
        return self.build_discord_report(period_days=7)

    def build_monthly_discord_report(self) -> WeeklyDiscordReportResponse:
        """Return a rolling twenty-eight-day Discord event report."""
        return self.build_discord_report(period_days=28)

    def build_discord_report(self, *, period_days: int) -> WeeklyDiscordReportResponse:
        """Return a rolling Discord event report for the requested period."""
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=period_days)
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
            "## Recommandations de stabilisation Discord",
            "",
            *self._stabilization_recommendations(report),
            "",
            "## Prochaines actions conseillees sur incidents",
            "",
            *self._incident_action_plan(report),
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
            action_plan=self._incident_action_plan(report),
        )

    def build_monthly_discord_management_pdf(self) -> bytes:
        """Return a polished monthly PDF report suitable for operational management."""
        report = self.build_monthly_discord_report()
        return build_weekly_discord_pdf(
            report,
            findings=self._management_findings(report),
            recommendations=self._stabilization_recommendations(report),
            action_plan=self._incident_action_plan(report),
        )

    @staticmethod
    def _security_advisories() -> list[WeeklyDiscordSecurityAdvisoryResponse]:
        """Return current security watch items for the AlertHub runtime stack."""
        return [
            WeeklyDiscordSecurityAdvisoryResponse(
                component="Vite dev server",
                current_version="6.4.3",
                severity="Low",
                status="Patched",
                finding=(
                    "The Vite 6 development server has been upgraded past the vulnerable 6.0.x "
                    "branch. Production still serves static files through Nginx."
                ),
                recommendation=(
                    "Keep the dev server local-only, keep npm audit in CI, and never expose .env "
                    "or source maps from development environments."
                ),
                reference="npm audit / Vite advisories",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="Nginx reverse proxy",
                current_version="1.30.3-alpine",
                severity="Low",
                status="Patched",
                finding=(
                    "The reverse proxy image has been moved from 1.27-alpine to a patched "
                    "1.30.x Alpine image."
                ),
                recommendation=(
                    "Pin images by digest in production, rebuild regularly, and keep security "
                    "headers enabled at the edge."
                ),
                reference="nginx.org security advisories",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="PostgreSQL",
                current_version="16.14-alpine",
                severity="Low",
                status="Pinned minor release",
                finding=(
                    "The PostgreSQL image is pinned to a current 16.x minor release instead of "
                    "the floating major tag."
                ),
                recommendation=(
                    "Verify backups before every database image upgrade, then apply Alembic "
                    "migrations only after PostgreSQL is healthy."
                ),
                reference="PostgreSQL security information",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="FastAPI / Starlette stack",
                current_version="FastAPI 0.139.0 / Uvicorn 0.51.0",
                severity="Low",
                status="Upgraded and monitored",
                finding=(
                    "The ASGI stack has been upgraded. Dependency auditing remains important "
                    "because FastAPI pulls Starlette transitively."
                ),
                recommendation=(
                    "Run pip-audit in CI, keep FastAPI-compatible Starlette updates current, "
                    "and keep trusted host/proxy headers strict at the edge."
                ),
                reference="FastAPI and Starlette advisories",
            ),
            WeeklyDiscordSecurityAdvisoryResponse(
                component="Secrets and Discord token",
                current_version="Environment-based secrets",
                severity="High",
                status="Rotate in Discord portal",
                finding=(
                    "Discord tokens, database credentials, and JWT secrets are environment "
                    "secrets. Exposure would allow bot abuse or data access."
                ),
                recommendation=(
                    "Rotate the Discord bot token in the Discord Developer Portal, update .env "
                    "through the admin connector screen, restart services, and keep .env out of Git."
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
        recommendations: list[str] = []

        if report.open_events:
            recommendations.append(
                f"- Traiter en priorite les {report.open_events} probleme(s) Discord encore "
                "ouverts, en commencant par les alertes critiques ou anciennes."
            )
            recommendations.append(
                "- Affecter un responsable a chaque probleme ouvert et suivre l'escalade "
                "jusqu'a resolution confirmee dans Discord."
            )

        critical_count = sum(
            metric.value
            for metric in report.by_severity
            if metric.label.lower() in {"critical", "critique", "disaster", "high"}
        )
        if critical_count:
            recommendations.append(
                f"- Isoler les {critical_count} alerte(s) de severite elevee et verifier "
                "immediatement la disponibilite des hosts concernes."
            )

        if report.by_host:
            top_host = report.by_host[0]
            recommendations.append(
                f"- Concentrer l'analyse de stabilite sur {top_host.label}, qui concentre "
                f"{top_host.value} evenement(s) Discord sur la periode."
            )

        if report.data_quality.unnamed_events or report.data_quality.unknown_host_events:
            recommendations.append(
                "- Normaliser les messages Discord entrants pour extraire systematiquement "
                "host, severite, statut, liens et nom du probleme."
            )

        if not recommendations and report.total_events:
            recommendations.append(
                "- Aucun incident ouvert majeur sur la periode: maintenir la surveillance du "
                "salon Discord et confirmer les resolutions dans les prochains rapports."
            )
        if not recommendations:
            recommendations.append(
                "- Aucun evenement Discord exploitable sur la periode: verifier que le bot lit "
                "le salon d'alertes attendu avant la prochaine synthese."
            )
        return recommendations

    def _incident_action_plan(
        self,
        report: WeeklyDiscordReportResponse,
    ) -> list[str]:
        if report.open_problems:
            actions = [
                (
                    f"- Escalader {problem.title} sur {problem.host or 'host non detecte'} "
                    f"vers {problem.escalation_owner or 'un responsable a designer'}; "
                    f"age incident: {problem.age_label}."
                )
                for problem in report.open_problems[:5]
            ]
            actions.append(
                "- Mettre a jour le message Discord d'origine avec le statut de traitement "
                "afin que le prochain rapport distingue clairement ouvert et resolu."
            )
            return actions

        if report.recent_events:
            return [
                "- Confirmer dans Discord que les derniers evenements resolus ne se repetent pas.",
                "- Conserver les liens d'incident dans les messages Discord pour faciliter les "
                "prochains exports."
            ]

        return [
            "- Publier un message de test dans le salon Discord d'alertes pour valider la chaine "
            "de collecte avant le prochain rapport."
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
