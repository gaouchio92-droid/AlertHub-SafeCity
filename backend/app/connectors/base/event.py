"""Common normalized event model for every connector."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ConnectorEvent(BaseModel):
    """Canonical event shape produced by all event-source connectors."""

    model_config = ConfigDict(frozen=True)

    source: str
    problem_id: str | None = None
    host: str | None = None
    severity: str | None = None
    status: str | None = None
    problem_name: str | None = None
    started_at: datetime | None = None
    resolved_at: datetime | None = None
    duration: int | None = None
    raw_payload: dict[str, Any]
