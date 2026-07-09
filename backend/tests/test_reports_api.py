"""Report API endpoint tests."""

from collections.abc import Iterator

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.v1.endpoints import reports as reports_endpoint
from app.core.config.settings import Settings
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


class StubDiscordReportPublisher:
    """Test double for Discord report delivery."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def publish_pdf(
        self,
        content: bytes,
        *,
        filename: str,
        summary: str,
    ) -> object:
        """Return a deterministic delivery object."""
        assert content.startswith(b"%PDF")
        assert filename == "alerthub-weekly-discord-report.pdf"
        assert "AlertHub Safe City" in summary
        return type(
            "Delivery",
            (),
            {
                "delivered": True,
                "channel_id": self._settings.discord_channel_id,
                "message_id": "discord-message-1",
                "filename": filename,
            },
        )()


def fake_db() -> Iterator[object]:
    """Yield a fake database dependency."""
    yield object()


def fake_settings() -> Settings:
    """Return Discord-ready test settings."""
    return Settings(
        secret_key="test-secret-key-with-at-least-32-chars",
        postgres_password="test-postgres-password",
        jwt_secret="test-jwt-secret-with-at-least-32-chars",
        discord_token="test-discord-token",
        discord_channel_id="1234567890",
    )


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


def test_weekly_discord_report_can_be_pushed_to_discord(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(reports_endpoint, "ReportService", StubReportService)
    monkeypatch.setattr(
        reports_endpoint,
        "DiscordReportPublisher",
        StubDiscordReportPublisher,
    )
    app.dependency_overrides[reports_endpoint.get_db] = fake_db
    app.dependency_overrides[reports_endpoint.get_settings] = fake_settings
    app.dependency_overrides[reports_endpoint.require_report_push] = lambda: object()
    client = TestClient(app)

    try:
        response = client.post("/api/v1/reports/weekly-discord/push-discord")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "delivered": True,
        "channel_id": "1234567890",
        "message_id": "discord-message-1",
        "filename": "alerthub-weekly-discord-report.pdf",
    }
