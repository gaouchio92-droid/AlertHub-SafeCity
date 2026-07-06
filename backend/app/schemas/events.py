"""Event API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventResponse(BaseModel):
    """Event returned by the API."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: UUID
    source: str
    problem_id: str | None
    host: str | None
    severity: str | None
    status: str | None
    problem_name: str | None
    started_at: datetime | None
    resolved_at: datetime | None
    duration: int | None
    raw_payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    """Paginated event list response."""

    model_config = ConfigDict(frozen=True)

    items: list[EventResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
