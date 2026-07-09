"""PDF rendering for management reports."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.reports import (
    WeeklyDiscordReportMetricResponse,
    WeeklyDiscordReportResponse,
)

PRIMARY = colors.HexColor("#06B6D4")
DARK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#64748B")
PANEL = colors.HexColor("#F8FAFC")
EMERALD = colors.HexColor("#10B981")
ROSE = colors.HexColor("#F43F5E")
AMBER = colors.HexColor("#F59E0B")
INDIGO = colors.HexColor("#6366F1")
CONTENT_WIDTH = 26.9 * cm


class BarChart(Flowable):  # type: ignore[misc]
    """Compact horizontal bar chart for report metrics."""

    def __init__(
        self,
        metrics: list[WeeklyDiscordReportMetricResponse],
        *,
        width: float,
        bar_color: Any,
        max_rows: int = 8,
    ) -> None:
        super().__init__()
        self.metrics = metrics[:max_rows]
        self.width = width
        self.bar_color = bar_color
        self.height = max(len(self.metrics), 1) * 22 + 14

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        return min(self.width, avail_width), self.height

    def draw(self) -> None:
        if not self.metrics:
            self.canv.setFillColor(MUTED)
            self.canv.drawString(0, self.height - 12, "Aucune donnee disponible")
            return

        max_value = max(metric.value for metric in self.metrics) or 1
        label_width = self.width * 0.45
        chart_width = self.width - label_width - 36
        y = self.height - 18
        for metric in self.metrics:
            bar_width = max((metric.value / max_value) * chart_width, 4)
            self.canv.setFillColor(DARK)
            self.canv.setFont("Helvetica", 8)
            self.canv.drawString(0, y + 3, _truncate(metric.label, 30))
            self.canv.setFillColor(colors.HexColor("#E2E8F0"))
            self.canv.roundRect(label_width, y, chart_width, 9, 3, stroke=0, fill=1)
            self.canv.setFillColor(self.bar_color)
            self.canv.roundRect(label_width, y, bar_width, 9, 3, stroke=0, fill=1)
            self.canv.setFillColor(DARK)
            self.canv.setFont("Helvetica-Bold", 8)
            self.canv.drawRightString(self.width, y + 2, str(metric.value))
            y -= 22


class DailyTrendChart(Flowable):  # type: ignore[misc]
    """Vertical daily trend chart."""

    def __init__(self, report: WeeklyDiscordReportResponse, *, width: float) -> None:
        super().__init__()
        self.report = report
        self.width = width
        self.height = 150

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        return min(self.width, avail_width), self.height

    def draw(self) -> None:
        items = self.report.daily_trend
        if not items:
            self.canv.setFillColor(MUTED)
            self.canv.drawString(0, self.height - 12, "Aucune tendance disponible")
            return

        max_value = max(item.total for item in items) or 1
        slot_width = self.width / len(items)
        chart_height = 105
        baseline = 26
        self.canv.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.canv.line(0, baseline, self.width, baseline)

        for index, item in enumerate(items):
            x = index * slot_width + slot_width * 0.24
            problem_height = max((item.problem / max_value) * chart_height, 2)
            resolved_height = max((item.resolved / max_value) * chart_height, 2)
            bar_width = max(slot_width * 0.18, 4)
            self.canv.setFillColor(ROSE)
            self.canv.roundRect(x, baseline, bar_width, problem_height, 2, stroke=0, fill=1)
            self.canv.setFillColor(EMERALD)
            self.canv.roundRect(
                x + bar_width + 2,
                baseline,
                bar_width,
                resolved_height,
                2,
                stroke=0,
                fill=1,
            )
            self.canv.setFillColor(DARK)
            self.canv.setFont("Helvetica", 7)
            self.canv.drawCentredString(
                index * slot_width + slot_width / 2,
                8,
                item.date.strftime("%d/%m"),
            )
            self.canv.setFont("Helvetica-Bold", 7)
            self.canv.drawCentredString(
                index * slot_width + slot_width / 2,
                baseline + max(problem_height, resolved_height) + 5,
                str(item.total),
            )


def build_weekly_discord_pdf(
    report: WeeklyDiscordReportResponse,
    *,
    findings: list[str],
    recommendations: list[str],
) -> bytes:
    """Render a polished management PDF for the weekly Discord report."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="Rapport hebdomadaire AlertHub Safe City",
        author="AlertHub Safe City",
    )
    styles = _styles()
    content: list[Flowable] = []
    readable_events = max(report.total_events - report.data_quality.unnamed_events, 0)

    content.extend(
        [
            _cover_header(styles),
            Spacer(1, 16),
            Paragraph("Rapport hebdomadaire de supervision", styles["Title"]),
            Paragraph("AlertHub Safe City", styles["Subtitle"]),
            Spacer(1, 8),
            Paragraph(
                (
                    f"Periode analysee : {report.period_start:%d/%m/%Y %H:%M UTC} "
                    f"au {report.period_end:%d/%m/%Y %H:%M UTC}"
                ),
                styles["Body"],
            ),
            Spacer(1, 18),
            _kpi_grid(
                [
                    ("Messages Discord", report.total_events, PRIMARY),
                    ("Alertes lisibles", readable_events, INDIGO),
                    (
                        "Problemes ouverts",
                        report.open_events,
                        ROSE if report.open_events else EMERALD,
                    ),
                    ("Problemes resolus", report.resolved_events, EMERALD),
                ]
            ),
            Spacer(1, 18),
            _section_title("Synthese executive", styles),
            *_bullet_list(findings, styles),
            Spacer(1, 12),
            _section_title("Tendance quotidienne", styles),
            DailyTrendChart(report, width=CONTENT_WIDTH),
            PageBreak(),
            _section_title("Equipements les plus impactes", styles),
            BarChart(report.by_host, width=CONTENT_WIDTH, bar_color=PRIMARY),
            Spacer(1, 18),
            _section_title("Repartition par severite", styles),
            BarChart(report.by_severity, width=CONTENT_WIDTH, bar_color=AMBER),
            Spacer(1, 18),
            _section_title("Problemes non resolus prioritaires", styles),
            _open_problems_table(report),
            Spacer(1, 18),
            _section_title("Derniers evenements significatifs", styles),
            _events_table(report),
            PageBreak(),
            _section_title("Veille securite applicative", styles),
            _security_advisories_table(report),
            Spacer(1, 18),
            _section_title("Recommandations de stabilisation", styles),
            _recommendation_cards(recommendations, styles),
            Spacer(1, 18),
            _section_title("Plan d'action conseille", styles),
            *_bullet_list(
                [
                    "Planifier une revue quotidienne des problemes ouverts.",
                    "Confirmer que le bot Discord lit le bon salon d'alertes.",
                    "Standardiser le format des messages emis par la supervision.",
                    "Surveiller les erreurs backend et la sante Docker apres chaque deploiement.",
                ],
                styles,
            ),
            Spacer(1, 20),
            Paragraph("Rapport genere automatiquement par AlertHub Safe City.", styles["Muted"]),
        ]
    )

    document.build(content, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    return buffer.getvalue()


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=30,
            textColor=DARK,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=PRIMARY,
            spaceAfter=8,
        ),
        "Heading": ParagraphStyle(
            "Heading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=DARK,
            spaceAfter=8,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#334155"),
        ),
        "Muted": ParagraphStyle(
            "Muted",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "CardLabel": ParagraphStyle(
            "CardLabel",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "CardValue": ParagraphStyle(
            "CardValue",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.black,
            wordWrap="CJK",
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
            wordWrap="CJK",
        ),
    }


def _cover_header(styles: dict[str, ParagraphStyle]) -> Table:
    return Table(
        [[Paragraph("ALERTHUB", styles["CardLabel"]), Paragraph("Safe City", styles["Body"])]],
        colWidths=[4.2 * cm, CONTENT_WIDTH - 4.2 * cm],
        rowHeights=[1.1 * cm],
        style=[
            ("BACKGROUND", (0, 0), (0, 0), DARK),
            ("BACKGROUND", (1, 0), (1, 0), PANEL),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ],
    )


def _kpi_grid(items: list[tuple[str, int, Any]]) -> Table:
    cells = [
        [
            Paragraph(str(value), _styles()["CardValue"]),
            Paragraph(label, _styles()["CardLabel"]),
        ]
        for label, value, _color in items
    ]
    table = Table(
        [[Table([[cell[0]], [cell[1]]], rowHeights=[0.65 * cm, 0.45 * cm]) for cell in cells]],
        colWidths=[CONTENT_WIDTH / 4] * 4,
    )
    style: list[tuple[object, ...]] = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for index, (_label, _value, color) in enumerate(items):
        style.append(("BACKGROUND", (index, 0), (index, 0), color))
        style.append(("BOX", (index, 0), (index, 0), 0.5, colors.white))
    table.setStyle(TableStyle(style))
    return table


def _section_title(title: str, styles: dict[str, ParagraphStyle]) -> KeepTogether:
    return KeepTogether(
        [
            Paragraph(title, styles["Heading"]),
            Table(
                [[""]],
                colWidths=[CONTENT_WIDTH],
                rowHeights=[0.05 * cm],
                style=[("BACKGROUND", (0, 0), (-1, -1), PRIMARY)],
            ),
            Spacer(1, 8),
        ]
    )


def _bullet_list(items: list[str], styles: dict[str, ParagraphStyle]) -> list[Paragraph]:
    return [
        Paragraph(f"- {item.removeprefix('- ').strip()}", styles["Body"])
        for item in items
    ]


def _events_table(report: WeeklyDiscordReportResponse) -> Table:
    styles = _styles()
    rows = [
        [
            _th("Evenement", styles),
            _th("Host", styles),
            _th("Severite", styles),
            _th("Statut", styles),
        ]
    ]
    for event in report.recent_events[:8]:
        rows.append(
            [
                _td(event.title, styles),
                _td(event.host or "Non detecte", styles),
                _td(event.severity or "Non detectee", styles),
                _td(event.status or "unknown", styles),
            ]
        )
    if len(rows) == 1:
        rows.append(
            [
                _td("Aucun evenement recent", styles),
                _td("-", styles),
                _td("-", styles),
                _td("-", styles),
            ]
        )
    table = Table(rows, colWidths=[14 * cm, 6 * cm, 3.5 * cm, 3.4 * cm], repeatRows=1)
    table.setStyle(_table_style())
    return table


def _open_problems_table(report: WeeklyDiscordReportResponse) -> Table:
    styles = _styles()
    rows = [
        [
            _th("Probleme", styles),
            _th("Host", styles),
            _th("Severite", styles),
            _th("Age", styles),
            _th("Action conseillee", styles),
        ]
    ]
    for problem in report.open_problems[:10]:
        rows.append(
            [
                _td(problem.title, styles),
                _td(problem.host or "Non detecte", styles),
                _td(problem.severity or "Non detectee", styles),
                _td(problem.age_label, styles),
                _td(problem.recommended_action, styles),
            ]
        )
    if len(rows) == 1:
        rows.append([
            _td("Aucun probleme non resolu", styles),
            _td("-", styles),
            _td("-", styles),
            _td("-", styles),
            _td("-", styles),
        ])
    table = Table(
        rows,
        colWidths=[10.2 * cm, 5.2 * cm, 3 * cm, 2.4 * cm, 6.1 * cm],
        repeatRows=1,
    )
    table.setStyle(_table_style())
    return table


def _security_advisories_table(report: WeeklyDiscordReportResponse) -> Table:
    styles = _styles()
    rows = [
        [
            _th("Composant", styles),
            _th("Severite", styles),
            _th("Statut", styles),
            _th("Risque observe", styles),
            _th("Solution recommandee", styles),
        ]
    ]
    for advisory in report.security_advisories:
        rows.append(
            [
                _td(f"{advisory.component}\n{advisory.current_version}", styles),
                _td(advisory.severity, styles),
                _td(advisory.status, styles),
                _td(advisory.finding, styles),
                _td(advisory.recommendation, styles),
            ]
        )
    if len(rows) == 1:
        rows.append([
            _td("Aucune alerte", styles),
            _td("-", styles),
            _td("-", styles),
            _td("-", styles),
            _td("-", styles),
        ])
    table = Table(
        rows,
        colWidths=[4.3 * cm, 2.3 * cm, 3.2 * cm, 8.2 * cm, 8.9 * cm],
        repeatRows=1,
    )
    table.setStyle(_table_style())
    return table


def _recommendation_cards(
    recommendations: list[str],
    styles: dict[str, ParagraphStyle],
) -> Table:
    rows = [
        [Paragraph(recommendation.removeprefix("- ").strip(), styles["Body"])]
        for recommendation in recommendations
    ]
    table = Table(rows, colWidths=[CONTENT_WIDTH])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PANEL),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _legend() -> Table:
    table = Table(
        [["Problemes ouverts", "Problemes resolus"]],
        colWidths=[4 * cm, 4 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("TEXTCOLOR", (0, 0), (0, 0), ROSE),
                ("TEXTCOLOR", (1, 0), (1, 0), EMERALD),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, -1), PANEL),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )


def _draw_footer(canvas: Any, document: Any) -> None:
    canvas_obj = canvas
    doc = document
    canvas_obj.saveState()
    canvas_obj.setFillColor(MUTED)
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawString(1.4 * cm, 0.7 * cm, "AlertHub Safe City")
    canvas_obj.drawRightString(28.3 * cm, 0.7 * cm, f"Page {doc.page}")
    canvas_obj.restoreState()


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[: max_length - 3]}..."


def _th(value: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(_escape_for_pdf(value), styles["TableHeader"])


def _td(value: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(_escape_for_pdf(value), styles["TableCell"])


def _escape_for_pdf(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
