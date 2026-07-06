"""Abstract connector interface."""

from abc import ABC, abstractmethod
from typing import Any

from app.connectors.base.event import ConnectorEvent
from app.connectors.base.status import ConnectorStatus


class BaseConnector(ABC):
    """Contract implemented by every event-source connector."""

    source: str
    display_name: str
    enabled: bool

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self._connected = False

    @property
    def connected(self) -> bool:
        """Return the connector connection state."""
        return self._connected

    @abstractmethod
    async def connect(self) -> None:
        """Initialize connector resources."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Release connector resources."""

    @abstractmethod
    async def health(self) -> ConnectorStatus:
        """Return current connector health."""

    @abstractmethod
    async def collect(self) -> list[dict[str, Any]]:
        """Collect raw event payloads from the source."""

    @abstractmethod
    async def sync(self) -> list[ConnectorEvent]:
        """Synchronize source events into normalized connector events."""

    @abstractmethod
    def parse(self, payload: dict[str, Any]) -> ConnectorEvent:
        """Normalize one raw payload into the common event model."""
