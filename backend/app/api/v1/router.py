"""API router composition."""

from fastapi import APIRouter

from app.api.v1.endpoints import connectors, events, health, reports

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(connectors.router, prefix="/connectors", tags=["connectors"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
