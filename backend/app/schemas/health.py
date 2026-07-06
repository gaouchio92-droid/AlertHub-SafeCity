"""Health endpoint schemas."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ServiceStatus(StrEnum):
    """Supported service health states."""

    OK = "ok"


class HealthCheck(BaseModel):
    """Health-check response payload."""

    model_config = ConfigDict(frozen=True)

    status: ServiceStatus
    app_name: str
    environment: str
    database: ServiceStatus
