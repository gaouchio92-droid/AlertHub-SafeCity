"""Scheduled connector synchronization job."""

from __future__ import annotations

import asyncio
import signal

from app.connectors.manager import connector_manager
from app.core.config.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import SessionLocal, dispose_engine
from app.services.events import EventService

logger = get_logger(__name__)


class SyncScheduler:
    """Run connector synchronization on a fixed interval."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        """Start the scheduler loop until shutdown is requested."""
        await connector_manager.start()
        logger.info(
            "Connector sync scheduler started",
            extra={"interval_seconds": self._settings.sync_interval_seconds},
        )
        try:
            while not self._stop_event.is_set():
                await self._sync_once()
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._settings.sync_interval_seconds,
                    )
                except TimeoutError:
                    continue
        finally:
            await connector_manager.stop()
            dispose_engine()
            logger.info("Connector sync scheduler stopped")

    def stop(self) -> None:
        """Request graceful shutdown."""
        self._stop_event.set()

    async def _sync_once(self) -> None:
        connector_events = await connector_manager.sync()
        with SessionLocal() as db:
            result = EventService(db).upsert_connector_events(connector_events)
        logger.info(
            "Scheduled connector sync completed",
            extra={
                "sync_received": result.received,
                "sync_created": result.created,
                "sync_updated": result.updated,
            },
        )


async def _main() -> None:
    configure_logging()
    scheduler = SyncScheduler()
    running_loop = asyncio.get_running_loop()
    for signal_name in (signal.SIGINT, signal.SIGTERM):
        running_loop.add_signal_handler(signal_name, scheduler.stop)
    await scheduler.run()


if __name__ == "__main__":
    asyncio.run(_main())
