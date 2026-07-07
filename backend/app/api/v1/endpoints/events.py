"""Event endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.connectors.manager import connector_manager
from app.database.session import get_db
from app.schemas.events import (
    EventListResponse,
    EventResponse,
    EventSummaryResponse,
    EventSyncResponse,
)
from app.services.events import EventService

router = APIRouter()


@router.get("/summary", response_model=EventSummaryResponse, summary="Event summary")
def event_summary(
    db: Annotated[Session, Depends(get_db)],
) -> EventSummaryResponse:
    """Return operational counters for stored connector events."""
    summary = EventService(db).summarize_events()
    return EventSummaryResponse.model_validate(summary)


@router.get("", response_model=EventListResponse, summary="List normalized events")
def list_events(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    source: Annotated[str | None, Query(max_length=64)] = None,
    status: Annotated[str | None, Query(max_length=64)] = None,
    severity: Annotated[str | None, Query(max_length=64)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    include_unparsed: bool = False,
) -> EventListResponse:
    """Return normalized events stored by connector ingestion."""
    events, total = EventService(db).list_events(
        limit=limit,
        offset=offset,
        source=source,
        status=status,
        severity=severity,
        query=q,
        include_unparsed=include_unparsed,
    )
    return EventListResponse(
        items=[EventResponse.model_validate(event) for event in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/sync", response_model=EventSyncResponse, summary="Sync connector events")
async def sync_events(
    db: Annotated[Session, Depends(get_db)],
) -> EventSyncResponse:
    """Collect events from active connectors and persist them locally."""
    connector_events = await connector_manager.sync()
    result = EventService(db).upsert_connector_events(connector_events)
    return EventSyncResponse(
        received=result.received,
        created=result.created,
        updated=result.updated,
    )
