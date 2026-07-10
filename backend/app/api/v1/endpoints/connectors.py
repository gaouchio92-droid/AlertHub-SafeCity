"""Connector status endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_admin
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
    ConnectorEnvironmentResponse,
    ConnectorEnvironmentUpdateRequest,
    ConnectorEnvironmentValueResponse,
    ConnectorRuntimeResponse,
    ConnectorStatusResponse,
    EventModelFieldResponse,
    EventModelResponse,
)
from app.services.environment import ConnectorEnvironmentService

router = APIRouter(dependencies=[Depends(require_admin)])


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
            env_template=[
                "EVENT_SOURCE=discord",
                "ENABLE_DISCORD=true",
                "ENABLE_ZABBIX_API=false",
                "ENABLE_ZABBIX_DB=false",
                "DISCORD_TOKEN=<discord-bot-token>",
                "DISCORD_GUILD_ID=<discord-server-id>",
                "DISCORD_CHANNEL_ID=<discord-channel-id>",
            ],
            apply_commands=[
                "docker compose up -d --force-recreate backend nginx",
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
                "ZABBIX_WEB_URL",
                "ZABBIX_USERNAME",
                "ZABBIX_PASSWORD",
            ],
            env_template=[
                "EVENT_SOURCE=zabbix_api",
                "ENABLE_DISCORD=false",
                "ENABLE_ZABBIX_API=true",
                "ENABLE_ZABBIX_DB=false",
                "ZABBIX_API_URL=https://zabbix.example.com/api_jsonrpc.php",
                "ZABBIX_WEB_URL=https://zabbix.example.com",
                "ZABBIX_USERNAME=<zabbix-user>",
                "ZABBIX_PASSWORD=<zabbix-password>",
            ],
            apply_commands=[
                "docker compose up -d --force-recreate backend nginx",
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
            env_template=[
                "EVENT_SOURCE=zabbix_database",
                "ENABLE_DISCORD=false",
                "ENABLE_ZABBIX_API=false",
                "ENABLE_ZABBIX_DB=true",
                "ZABBIX_DB_HOST=<zabbix-db-host>",
                "ZABBIX_DB_PORT=5432",
                "ZABBIX_DB_NAME=<zabbix-db-name>",
                "ZABBIX_DB_USER=<read-only-user>",
                "ZABBIX_DB_PASSWORD=<read-only-password>",
            ],
            apply_commands=[
                "docker compose up -d --force-recreate backend nginx",
            ],
            restart_required=True,
            note=(
                "Optional read-only connector. The platform must never modify "
                "the Zabbix database."
            ),
        ),
    ]


@router.get(
    "/environment",
    response_model=ConnectorEnvironmentResponse,
    summary="Connector environment settings",
)
async def connector_environment() -> ConnectorEnvironmentResponse:
    """Return sanitized connector environment values."""
    values = ConnectorEnvironmentService().values()
    return ConnectorEnvironmentResponse(
        values=[ConnectorEnvironmentValueResponse.model_validate(value) for value in values],
        restart_required=True,
        apply_command="docker compose up -d --force-recreate backend scheduler nginx",
    )


@router.put(
    "/environment",
    response_model=ConnectorEnvironmentResponse,
    summary="Update connector environment settings",
)
async def update_connector_environment(
    payload: ConnectorEnvironmentUpdateRequest,
) -> ConnectorEnvironmentResponse:
    """Persist connector environment values to the mounted .env file."""
    try:
        values = ConnectorEnvironmentService().update(payload.values)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return ConnectorEnvironmentResponse(
        values=[ConnectorEnvironmentValueResponse.model_validate(value) for value in values],
        restart_required=True,
        apply_command="docker compose up -d --force-recreate backend scheduler nginx",
    )
