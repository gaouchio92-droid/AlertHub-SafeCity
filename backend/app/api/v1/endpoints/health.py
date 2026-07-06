"""Health-check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config.settings import Settings, get_settings
from app.database.session import get_db
from app.schemas.health import HealthCheck, ServiceStatus

router = APIRouter()


@router.get("", response_model=HealthCheck, summary="Application health")
def health_check(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HealthCheck:
    """Return application and database health information."""
    db.execute(text("SELECT 1"))
    return HealthCheck(
        status=ServiceStatus.OK,
        app_name=settings.app_name,
        environment=settings.app_env,
        database=ServiceStatus.OK,
    )
