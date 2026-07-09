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
    operational_data: str | None
    links: list[str]
    escalation_priority: int | None
    escalation_level: str | None
    escalation_owner: str | None
    escalation_due_at: datetime | None
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


class EventSummaryMetricResponse(BaseModel):
    """Aggregated event count by one dimension."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    label: str
    value: int = Field(ge=0)


class EventSummaryResponse(BaseModel):
    """Operational event summary response."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    total_events: int = Field(ge=0)
    open_events: int = Field(ge=0)
    resolved_events: int = Field(ge=0)
    unparsed_events: int = Field(ge=0)
    last_event_at: datetime | None
    by_source: list[EventSummaryMetricResponse]
    by_status: list[EventSummaryMetricResponse]
    by_severity: list[EventSummaryMetricResponse]


class EventSyncResponse(BaseModel):
    """Connector event synchronization response."""

    model_config = ConfigDict(frozen=True)

    received: int = Field(ge=0)
    created: int = Field(ge=0)
    updated: int = Field(ge=0)
