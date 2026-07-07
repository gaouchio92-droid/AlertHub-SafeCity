"""Discord connector implementation."""

from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorEvent, ConnectorStatus
from app.connectors.discord.parser import parse_discord_zabbix_events
from app.core.config.settings import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DiscordConnector(BaseConnector):
    """Default connector for Discord-hosted alert messages."""

    source = "discord"
    display_name = "Discord"

    def __init__(self, settings: Settings) -> None:
        super().__init__(enabled=settings.enable_discord)
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """Prepare the Discord HTTP client."""
        if not self.enabled:
            return

        headers = {}
        if self._settings.discord_token:
            headers["Authorization"] = f"Bot {self._settings.discord_token}"

        self._client = httpx.AsyncClient(
            base_url="https://discord.com/api/v10",
            headers=headers,
            timeout=10.0,
        )
        self._connected = True
        logger.info("Discord connector loaded")

    async def disconnect(self) -> None:
        """Close the Discord HTTP client."""
        if self._client:
            await self._client.aclose()
        self._client = None
        self._connected = False

    async def health(self) -> ConnectorStatus:
        """Return Discord connector status."""
        return ConnectorStatus(
            name=self.display_name,
            enabled=self.enabled,
            connected=self.connected,
        )

    async def collect(self) -> list[dict[str, Any]]:
        """Read recent Discord channel messages when credentials are configured."""
        if not self.enabled or not self._client:
            return []
        if not self._settings.discord_token or not self._settings.discord_channel_id:
            return []

        response = await self._client.get(
            f"/channels/{self._settings.discord_channel_id}/messages",
            params={"limit": 50},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict)]

    async def sync(self) -> list[ConnectorEvent]:
        """Collect and normalize Discord messages."""
        events: list[ConnectorEvent] = []
        for payload in await self.collect():
            events.extend(parse_discord_zabbix_events(payload, source=self.source))
        return events

    def parse(self, payload: dict[str, Any]) -> ConnectorEvent:
        """Normalize one Discord message payload."""
        return parse_discord_zabbix_events(payload, source=self.source)[0]
