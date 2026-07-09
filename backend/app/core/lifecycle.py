"""Application startup and shutdown hooks."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.connectors.manager import connector_manager
from app.core.config.settings import get_settings
from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.database.session import dispose_engine
from app.services.identity import IdentityService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle resources."""
    logger.info("Starting AlertHub Safe City backend")
    with SessionLocal() as db:
        IdentityService(db).bootstrap(get_settings())
    await connector_manager.start()
    yield
    logger.info("Stopping AlertHub Safe City backend")
    await connector_manager.stop()
    dispose_engine()
