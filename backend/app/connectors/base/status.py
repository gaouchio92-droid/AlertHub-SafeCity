"""Connector status models."""

from pydantic import BaseModel, ConfigDict


class ConnectorStatus(BaseModel):
    """Runtime status for a connector."""

    model_config = ConfigDict(frozen=True)

    name: str
    enabled: bool
    connected: bool
