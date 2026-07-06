"""Connector catalog definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorCatalogItem:
    """Static connector catalog entry."""

    source: str
    name: str
    category: str
    implemented: bool
    default_enabled: bool
    description: str


CONNECTOR_CATALOG: tuple[ConnectorCatalogItem, ...] = (
    ConnectorCatalogItem(
        source="discord",
        name="Discord",
        category="default",
        implemented=True,
        default_enabled=True,
        description="Primary source for Discord server alert messages.",
    ),
    ConnectorCatalogItem(
        source="zabbix_api",
        name="Zabbix API",
        category="optional",
        implemented=True,
        default_enabled=False,
        description="Optional read-only synchronization through the Zabbix JSON-RPC API.",
    ),
    ConnectorCatalogItem(
        source="zabbix_database",
        name="Zabbix Database",
        category="optional",
        implemented=True,
        default_enabled=False,
        description="Optional read-only synchronization from a Zabbix PostgreSQL database.",
    ),
    ConnectorCatalogItem(
        source="rest_api",
        name="REST API",
        category="future",
        implemented=False,
        default_enabled=False,
        description="Reserved source for future external HTTP event ingestion.",
    ),
    ConnectorCatalogItem(
        source="syslog",
        name="Syslog",
        category="future",
        implemented=False,
        default_enabled=False,
        description="Reserved source for future network syslog event ingestion.",
    ),
    ConnectorCatalogItem(
        source="wazuh",
        name="Wazuh",
        category="future",
        implemented=False,
        default_enabled=False,
        description="Reserved source for future Wazuh security event ingestion.",
    ),
    ConnectorCatalogItem(
        source="grafana",
        name="Grafana",
        category="future",
        implemented=False,
        default_enabled=False,
        description="Reserved source for future Grafana alert ingestion.",
    ),
    ConnectorCatalogItem(
        source="cacti",
        name="Cacti",
        category="future",
        implemented=False,
        default_enabled=False,
        description="Reserved source for future Cacti monitoring event ingestion.",
    ),
)
