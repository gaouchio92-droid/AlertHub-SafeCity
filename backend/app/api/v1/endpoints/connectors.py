"""Connector status endpoints."""

from fastapi import APIRouter

from app.connectors.catalog import CONNECTOR_CATALOG
from app.connectors.diagnostics import build_connector_diagnostics
from app.connectors.event_model import EVENT_MODEL_FIELDS
from app.connectors.manager import connector_manager
from app.core.config.settings import get_settings
from app.schemas.connectors import (
    ConnectorCatalogItemResponse,
    ConnectorCatalogResponse,
    ConnectorConfigurationGuideItemResponse,
    ConnectorDiagnosticResponse,
    ConnectorRuntimeResponse,
    ConnectorStatusResponse,
    EventModelFieldResponse,
    EventModelResponse,
)

router = APIRouter()


@router.get("", response_model=list[ConnectorStatusResponse], summary="Connector status")
async def list_connectors() -> list[ConnectorStatusResponse]:
    """Return loaded connector statuses."""
    statuses = await connector_manager.statuses()
    return [ConnectorStatusResponse.model_validate(status) for status in statuses]


@router.get(
    "/catalog",
    response_model=ConnectorCatalogResponse,
    summary="Connector catalog",
)
async def connector_catalog() -> ConnectorCatalogResponse:
    """Return implemented and planned connector definitions."""
    settings = get_settings()
    return ConnectorCatalogResponse(
        event_source=settings.event_source,
        items=[ConnectorCatalogItemResponse.model_validate(item) for item in CONNECTOR_CATALOG],
    )


@router.get(
    "/event-model",
    response_model=EventModelResponse,
    summary="Common connector event model",
)
async def connector_event_model() -> EventModelResponse:
    """Return the normalized event contract implemented by every connector."""
    return EventModelResponse(
        name="ConnectorEvent",
        fields=[EventModelFieldResponse.model_validate(field) for field in EVENT_MODEL_FIELDS],
    )


@router.get(
    "/runtime",
    response_model=ConnectorRuntimeResponse,
    summary="Connector runtime configuration",
)
async def connector_runtime() -> ConnectorRuntimeResponse:
    """Return non-sensitive connector runtime settings."""
    settings = get_settings()
    source_flags = {
        "discord": settings.enable_discord,
        "zabbix_api": settings.enable_zabbix_api,
        "zabbix_database": settings.enable_zabbix_db,
    }
    return ConnectorRuntimeResponse(
        event_source=settings.event_source,
        multiple_mode=settings.event_source == "multiple",
        enabled_sources=[source for source, enabled in source_flags.items() if enabled],
        disabled_sources=[source for source, enabled in source_flags.items() if not enabled],
        dynamic_imports_configured=bool(settings.connector_imports.strip()),
    )


@router.get(
    "/diagnostics",
    response_model=list[ConnectorDiagnosticResponse],
    summary="Connector configuration diagnostics",
)
async def connector_diagnostics() -> list[ConnectorDiagnosticResponse]:
    """Return non-sensitive connector configuration diagnostics."""
    settings = get_settings()
    return [
        ConnectorDiagnosticResponse.model_validate(diagnostic)
        for diagnostic in build_connector_diagnostics(settings)
    ]


@router.get(
    "/configuration-guide",
    response_model=list[ConnectorConfigurationGuideItemResponse],
    summary="Connector configuration guide",
)
async def connector_configuration_guide() -> list[ConnectorConfigurationGuideItemResponse]:
    """Return non-sensitive environment configuration instructions."""
    return [
        ConnectorConfigurationGuideItemResponse(
            source="discord",
            name="Discord",
            env_vars=[
                "EVENT_SOURCE=discord",
                "ENABLE_DISCORD=true",
                "DISCORD_TOKEN",
                "DISCORD_CHANNEL_ID",
                "DISCORD_GUILD_ID",
            ],
            restart_required=True,
            note="Discord is the default connector. Values are read from .env and Docker Compose.",
        ),
        ConnectorConfigurationGuideItemResponse(
            source="zabbix_api",
            name="Zabbix API",
            env_vars=[
                "EVENT_SOURCE=zabbix_api",
                "ENABLE_ZABBIX_API=true",
                "ZABBIX_API_URL",
                "ZABBIX_USERNAME",
                "ZABBIX_PASSWORD",
            ],
            restart_required=True,
            note=(
                "Optional connector. Disabled by default and requires valid "
                "Zabbix API credentials."
            ),
        ),
        ConnectorConfigurationGuideItemResponse(
            source="zabbix_database",
            name="Zabbix Database",
            env_vars=[
                "EVENT_SOURCE=zabbix_database",
                "ENABLE_ZABBIX_DB=true",
                "ZABBIX_DB_HOST",
                "ZABBIX_DB_PORT",
                "ZABBIX_DB_NAME",
                "ZABBIX_DB_USER",
                "ZABBIX_DB_PASSWORD",
            ],
            restart_required=True,
            note=(
                "Optional read-only connector. The platform must never modify "
                "the Zabbix database."
            ),
        ),
    ]
