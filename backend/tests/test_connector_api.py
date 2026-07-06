"""Connector API endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_connector_runtime_endpoint_returns_non_sensitive_configuration() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/connectors/runtime")

    assert response.status_code == 200
    payload = response.json()
    assert payload["event_source"] == "discord"
    assert payload["multiple_mode"] is False
    assert "discord" in payload["enabled_sources"]
    assert "zabbix_api" in payload["disabled_sources"]
    assert "zabbix_database" in payload["disabled_sources"]
    assert "password" not in response.text.lower()


def test_connector_event_model_endpoint_returns_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/connectors/event-model")

    assert response.status_code == 200
    payload = response.json()
    fields = {field["name"] for field in payload["fields"]}
    assert payload["name"] == "ConnectorEvent"
    assert {"source", "raw_payload", "severity", "status"}.issubset(fields)


def test_connector_diagnostics_endpoint_returns_missing_configuration_without_secrets() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/connectors/diagnostics")

    assert response.status_code == 200
    payload = response.json()
    discord = next(item for item in payload if item["source"] == "discord")
    assert discord["enabled"] is True
    assert discord["ready"] is False
    assert "DISCORD_TOKEN" in discord["missing_configuration"]
    assert "DISCORD_CHANNEL_ID" in discord["missing_configuration"]
    assert "password" not in response.text.lower()


def test_connector_configuration_guide_endpoint_lists_env_vars_without_values() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/connectors/configuration-guide")

    assert response.status_code == 200
    payload = response.json()
    discord = next(item for item in payload if item["source"] == "discord")
    assert "DISCORD_TOKEN" in discord["env_vars"]
    assert discord["restart_required"] is True
    assert "Bot " not in response.text


def test_weekly_discord_report_status_is_explicitly_not_implemented() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/reports/weekly-discord/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["feature"] == "Weekly Discord report"
    assert payload["implemented"] is False
    assert payload["visible_in_ui"] is True
    assert any(
        "Discord message ingestion" in item
        for item in payload["required_before_available"]
    )
