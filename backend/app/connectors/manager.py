"""Connector manager."""

import asyncio

from app.connectors.base import BaseConnector, ConnectorEvent, ConnectorStatus
from app.connectors.factory import ConnectorFactory, build_connector_factory, import_connector_class
from app.core.config.settings import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectorManager:
    """Load, start, stop, and report connector status."""

    def __init__(
        self,
        settings: Settings,
        factory: ConnectorFactory | None = None,
    ) -> None:
        self._settings = settings
        self._factory = factory or build_connector_factory()
        self._connectors: list[BaseConnector] = []

    @property
    def connectors(self) -> tuple[BaseConnector, ...]:
        """Return loaded connector instances."""
        return tuple(self._connectors)

    def load(self) -> None:
        """Load connectors according to EVENT_SOURCE and enable flags."""
        self._register_configured_connectors()
        sources = self._selected_sources()
        self._connectors = [self._factory.create(source, self._settings) for source in sources]
        logger.info("Loaded connectors", extra={"sources": sources})

    async def start(self) -> None:
        """Load and connect enabled connectors."""
        self.load()
        await asyncio.gather(
            *(self._safe_connect(connector) for connector in self._active_connectors()),
        )

    async def stop(self) -> None:
        """Disconnect all loaded connectors."""
        for connector in self._connectors:
            await connector.disconnect()

    async def statuses(self) -> list[ConnectorStatus]:
        """Return statuses for all loaded connectors."""
        if not self._connectors:
            self.load()
        return [await connector.health() for connector in self._connectors]

    async def sync(self) -> list[ConnectorEvent]:
        """Collect normalized events from every active connector."""
        if not self._connectors:
            await self.start()
        results = await asyncio.gather(
            *(self._safe_sync(connector) for connector in self._active_connectors()),
        )
        return [event for connector_events in results for event in connector_events]

    def _selected_sources(self) -> tuple[str, ...]:
        configured_source = self._settings.event_source
        all_sources = self._factory.registered_sources()
        if configured_source == "multiple":
            return all_sources
        if configured_source not in all_sources:
            raise ValueError(f"Unsupported connector source: {configured_source}")
        return all_sources

    def _active_connectors(self) -> tuple[BaseConnector, ...]:
        configured_source = self._settings.event_source
        if configured_source == "multiple":
            return tuple(connector for connector in self._connectors if connector.enabled)
        return tuple(
            connector
            for connector in self._connectors
            if connector.enabled and connector.source == configured_source
        )

    async def _safe_connect(self, connector: BaseConnector) -> None:
        try:
            await connector.connect()
        except Exception:
            logger.exception("Connector failed to connect", extra={"source": connector.source})

    async def _safe_sync(self, connector: BaseConnector) -> list[ConnectorEvent]:
        try:
            return await connector.sync()
        except Exception:
            logger.exception("Connector sync failed", extra={"source": connector.source})
            return []

    def _register_configured_connectors(self) -> None:
        import_paths = [
            import_path.strip()
            for import_path in self._settings.connector_imports.split(",")
            if import_path.strip()
        ]
        for import_path in import_paths:
            self._factory.register_connector_class(import_connector_class(import_path))


connector_manager = ConnectorManager(get_settings())
