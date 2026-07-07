"""Report API endpoint tests."""

from collections.abc import Iterator

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.v1.endpoints import reports as reports_endpoint
from app.main import app


class StubReportService:
    """Test double for report exports."""

    def __init__(self, db: object) -> None:
        self._db = db

    def build_weekly_discord_management_report(self) -> str:
        """Return deterministic Markdown export content."""
        return "# Rapport hebdomadaire AlertHub Safe City\n\n## Recommandations\n"

    def build_weekly_discord_management_pdf(self) -> bytes:
        """Return deterministic PDF export content."""
        return b"%PDF-1.4\n% AlertHub test PDF\n"


def fake_db() -> Iterator[object]:
    """Yield a fake database dependency."""
    yield object()


def test_weekly_discord_export_returns_markdown_attachment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(reports_endpoint, "ReportService", StubReportService)
    app.dependency_overrides[reports_endpoint.get_db] = fake_db
    client = TestClient(app)

    try:
        response = client.get("/api/v1/reports/weekly-discord/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert "alerthub-weekly-discord-report.md" in response.headers["content-disposition"]
    assert "Rapport hebdomadaire AlertHub Safe City" in response.text


def test_weekly_discord_pdf_export_returns_pdf_attachment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(reports_endpoint, "ReportService", StubReportService)
    app.dependency_overrides[reports_endpoint.get_db] = fake_db
    client = TestClient(app)

    try:
        response = client.get("/api/v1/reports/weekly-discord/export.pdf")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "alerthub-weekly-discord-report.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
