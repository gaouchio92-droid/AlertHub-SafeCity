"""Connector engine tests."""

import asyncio

import pytest

from app.connectors.base import BaseConnector, ConnectorEvent, ConnectorStatus
from app.connectors.catalog import CONNECTOR_CATALOG
from app.connectors.event_model import EVENT_MODEL_FIELDS
from app.connectors.manager import ConnectorManager
from app.core.config.settings import Settings


class ImportedConnector(BaseConnector):
    """Connector used to verify dynamic import registration."""

    source = "imported"
    display_name = "Imported"

    def __init__(self, settings: Settings) -> None:
        super().__init__(enabled=True)
        self._settings = settings

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def health(self) -> ConnectorStatus:
        return ConnectorStatus(
            name=self.display_name,
            enabled=self.enabled,
            connected=self.connected,
        )

    async def collect(self) -> list[dict[str, object]]:
        return []

    async def sync(self) -> list[ConnectorEvent]:
        return []

    def parse(self, payload: dict[str, object]) -> ConnectorEvent:
        return ConnectorEvent(source=self.source, raw_payload=payload)


def build_settings(**overrides: object) -> Settings:
    """Build valid settings for connector manager tests."""
    values: dict[str, object] = {
        "secret_key": "test-secret-key-with-at-least-32-chars",
        "postgres_password": "postgres-password",
        "jwt_secret": "test-jwt-secret-with-at-least-32-chars",
    }
    values.update(overrides)
    return Settings(**values)


def test_default_connector_statuses_include_optional_sources() -> None:
    settings = build_settings()
    manager = ConnectorManager(settings)

    statuses = asyncio.run(manager.statuses())

    assert [status.name for status in statuses] == ["Discord", "Zabbix API", "Zabbix Database"]
    assert statuses[0].enabled is True
    assert statuses[1].enabled is False
    assert statuses[2].enabled is False


def test_default_source_only_connects_discord() -> None:
    settings = build_settings()
    manager = ConnectorManager(settings)

    asyncio.run(manager.start())
    statuses = asyncio.run(manager.statuses())

    assert [(status.name, status.connected) for status in statuses] == [
        ("Discord", True),
        ("Zabbix API", False),
        ("Zabbix Database", False),
    ]
    asyncio.run(manager.stop())


def test_multiple_source_connects_all_enabled_connectors() -> None:
    settings = build_settings(event_source="multiple", enable_zabbix_api=True)
    manager = ConnectorManager(settings)

    asyncio.run(manager.start())
    statuses = asyncio.run(manager.statuses())

    assert next(status for status in statuses if status.name == "Discord").connected is True
    assert next(status for status in statuses if status.name == "Zabbix API").connected is False
    asyncio.run(manager.stop())


def test_unsupported_event_source_fails_fast() -> None:
    settings = build_settings(event_source="not_registered")
    manager = ConnectorManager(settings)

    with pytest.raises(ValueError, match="Unsupported connector source"):
        manager.load()


def test_connector_imports_register_future_sources() -> None:
    settings = build_settings(
        event_source="imported",
        connector_imports="tests.test_connectors.ImportedConnector",
    )
    manager = ConnectorManager(settings)

    asyncio.run(manager.start())
    statuses = asyncio.run(manager.statuses())

    imported = next(status for status in statuses if status.name == "Imported")
    assert imported.enabled is True
    assert imported.connected is True
    asyncio.run(manager.stop())


def test_connector_catalog_lists_current_and_future_sources() -> None:
    sources = {item.source for item in CONNECTOR_CATALOG}

    assert {
        "discord",
        "zabbix_api",
        "zabbix_database",
        "rest_api",
        "syslog",
        "wazuh",
        "grafana",
        "cacti",
    }.issubset(sources)
    discord = next(item for item in CONNECTOR_CATALOG if item.source == "discord")
    rest_api = next(item for item in CONNECTOR_CATALOG if item.source == "rest_api")
    assert discord.default_enabled is True
    assert rest_api.implemented is False


def test_event_model_contract_contains_required_fields() -> None:
    fields = {field.name: field for field in EVENT_MODEL_FIELDS}

    assert {"source", "raw_payload"}.issubset(fields)
    assert fields["source"].required is True
    assert fields["raw_payload"].required is True
    assert {
        "problem_id",
        "host",
        "severity",
        "status",
        "problem_name",
        "started_at",
        "resolved_at",
        "duration",
    }.issubset(fields)
