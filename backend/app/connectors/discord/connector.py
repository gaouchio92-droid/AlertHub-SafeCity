"""Discord connector implementation."""

from datetime import datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorEvent, ConnectorStatus
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
        return [self.parse(payload) for payload in await self.collect()]

    def parse(self, payload: dict[str, Any]) -> ConnectorEvent:
        """Normalize one Discord message payload."""
        timestamp = payload.get("timestamp")
        started_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")) if timestamp else None
        author = payload.get("author") if isinstance(payload.get("author"), dict) else {}

        return ConnectorEvent(
            source=self.source,
            problem_id=str(payload.get("id")) if payload.get("id") else None,
            host=str(author.get("username")) if author.get("username") else None,
            severity=None,
            status="received",
            problem_name=str(payload.get("content"))[:255] if payload.get("content") else None,
            started_at=started_at,
            resolved_at=None,
            duration=None,
            raw_payload=payload,
        )
