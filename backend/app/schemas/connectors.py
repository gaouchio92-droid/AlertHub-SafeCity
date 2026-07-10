"""Connector API schemas."""

from pydantic import BaseModel, ConfigDict


class ConnectorStatusResponse(BaseModel):
    """Connector status response."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    name: str
    enabled: bool
    connected: bool


class ConnectorCatalogItemResponse(BaseModel):
    """Connector catalog item response."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    source: str
    name: str
    category: str
    implemented: bool
    default_enabled: bool
    description: str


class ConnectorCatalogResponse(BaseModel):
    """Connector catalog response."""

    model_config = ConfigDict(frozen=True)

    event_source: str
    items: list[ConnectorCatalogItemResponse]


class EventModelFieldResponse(BaseModel):
    """Common event model field response."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    name: str
    data_type: str
    required: bool
    description: str


class EventModelResponse(BaseModel):
    """Common event model response."""

    model_config = ConfigDict(frozen=True)

    name: str
    fields: list[EventModelFieldResponse]


class ConnectorRuntimeResponse(BaseModel):
    """Non-sensitive connector runtime configuration response."""

    model_config = ConfigDict(frozen=True)

    event_source: str
    multiple_mode: bool
    enabled_sources: list[str]
    disabled_sources: list[str]
    dynamic_imports_configured: bool


class ConnectorDiagnosticResponse(BaseModel):
    """Connector configuration diagnostic response."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    source: str
    name: str
    enabled: bool
    ready: bool
    missing_configuration: list[str]


class ConnectorConfigurationGuideItemResponse(BaseModel):
    """Connector configuration guide item."""

    model_config = ConfigDict(frozen=True)

    source: str
    name: str
    env_vars: list[str]
    env_template: list[str]
    apply_commands: list[str]
    restart_required: bool
    note: str


class ConnectorEnvironmentValueResponse(BaseModel):
    """Sanitized connector environment value."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    key: str
    value: str
    secret: bool
    configured: bool


class ConnectorEnvironmentResponse(BaseModel):
    """Connector environment settings response."""

    model_config = ConfigDict(frozen=True)

    values: list[ConnectorEnvironmentValueResponse]
    restart_required: bool
    apply_command: str


class ConnectorEnvironmentUpdateRequest(BaseModel):
    """Connector environment update payload."""

    model_config = ConfigDict(frozen=True)

    values: dict[str, str]
