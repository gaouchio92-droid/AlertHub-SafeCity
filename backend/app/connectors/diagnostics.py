"""Connector configuration diagnostics."""

from dataclasses import dataclass

from app.core.config.settings import Settings


@dataclass(frozen=True)
class ConnectorDiagnostic:
    """Non-sensitive connector configuration diagnostic."""

    source: str
    name: str
    enabled: bool
    ready: bool
    missing_configuration: list[str]


def build_connector_diagnostics(settings: Settings) -> list[ConnectorDiagnostic]:
    """Build connector configuration diagnostics without exposing secret values."""
    diagnostics = [
        _diagnostic(
            source="discord",
            name="Discord",
            enabled=settings.enable_discord,
            required_fields={
                "DISCORD_TOKEN": settings.discord_token,
                "DISCORD_CHANNEL_ID": settings.discord_channel_id,
            },
        ),
        _diagnostic(
            source="zabbix_api",
            name="Zabbix API",
            enabled=settings.enable_zabbix_api,
            required_fields={
                "ZABBIX_API_URL": settings.zabbix_api_url,
                "ZABBIX_USERNAME": settings.zabbix_username,
                "ZABBIX_PASSWORD": settings.zabbix_password,
            },
        ),
        _diagnostic(
            source="zabbix_database",
            name="Zabbix Database",
            enabled=settings.enable_zabbix_db,
            required_fields={
                "ZABBIX_DB_HOST": settings.zabbix_db_host,
                "ZABBIX_DB_NAME": settings.zabbix_db_name,
                "ZABBIX_DB_USER": settings.zabbix_db_user,
                "ZABBIX_DB_PASSWORD": settings.zabbix_db_password,
            },
        ),
    ]
    return diagnostics


def _diagnostic(
    *,
    source: str,
    name: str,
    enabled: bool,
    required_fields: dict[str, str],
) -> ConnectorDiagnostic:
    missing_configuration = [
        field_name for field_name, value in required_fields.items() if enabled and not value.strip()
    ]
    return ConnectorDiagnostic(
        source=source,
        name=name,
        enabled=enabled,
        ready=enabled and not missing_configuration,
        missing_configuration=missing_configuration,
    )
