"""Discord delivery service for generated management reports."""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx
from httpx._types import RequestFiles

from app.core.config.settings import Settings


@dataclass(frozen=True)
class DiscordReportDelivery:
    """Discord delivery result."""

    delivered: bool
    channel_id: str
    message_id: str | None
    filename: str


class DiscordReportPublisherError(RuntimeError):
    """Raised when a generated report cannot be delivered to Discord."""


class DiscordReportPublisher:
    """Publish generated report artifacts to the configured Discord channel."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    def publish_pdf(
        self,
        content: bytes,
        *,
        filename: str,
        summary: str,
    ) -> DiscordReportDelivery:
        """Send a PDF report to the configured Discord channel."""
        self._validate_configuration()
        channel_id = self._settings.discord_channel_id
        payload = {
            "content": summary,
            "attachments": [{"id": 0, "filename": filename}],
        }
        files: RequestFiles = [
            ("payload_json", (None, json.dumps(payload), "application/json")),
            ("files[0]", (filename, content, "application/pdf")),
        ]

        close_client = self._client is None
        client = self._client or httpx.Client(timeout=30)
        try:
            response = client.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={"Authorization": f"Bot {self._settings.discord_token}"},
                files=files,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise DiscordReportPublisherError(
                f"Discord rejected the report upload with status {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise DiscordReportPublisherError(
                "Discord report upload failed because the Discord API is unreachable."
            ) from exc
        finally:
            if close_client:
                client.close()

        payload_response = response.json()
        return DiscordReportDelivery(
            delivered=True,
            channel_id=channel_id,
            message_id=str(payload_response.get("id")) if payload_response.get("id") else None,
            filename=filename,
        )

    def _validate_configuration(self) -> None:
        if not self._settings.enable_discord:
            raise DiscordReportPublisherError("Discord connector is disabled.")
        if not self._settings.discord_token:
            raise DiscordReportPublisherError("DISCORD_TOKEN is not configured.")
        if not self._settings.discord_channel_id:
            raise DiscordReportPublisherError("DISCORD_CHANNEL_ID is not configured.")
