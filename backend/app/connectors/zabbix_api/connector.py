"""Zabbix API connector implementation."""

from datetime import UTC, datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ConnectorEvent, ConnectorStatus
from app.core.config.settings import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ZabbixApiConnector(BaseConnector):
    """Optional read-only connector for Zabbix JSON-RPC API data."""

    source = "zabbix_api"
    display_name = "Zabbix API"

    def __init__(self, settings: Settings) -> None:
        super().__init__(enabled=settings.enable_zabbix_api)
        self._settings = settings
        self._client: httpx.AsyncClient | None = None
        self._auth_token: str | None = None
        self._last_event_clock: int | None = None

    async def connect(self) -> None:
        """Authenticate to the Zabbix API when enabled."""
        if not self.enabled:
            return
        if not (
            self._settings.zabbix_api_url
            and self._settings.zabbix_username
            and self._settings.zabbix_password
        ):
            logger.warning("Zabbix API connector enabled but missing credentials")
            return

        self._client = httpx.AsyncClient(base_url=self._settings.zabbix_api_url, timeout=20.0)
        self._auth_token = await self.authenticate()
        self._connected = bool(self._auth_token)

    async def disconnect(self) -> None:
        """Close Zabbix API resources."""
        if self._client:
            await self._client.aclose()
        self._client = None
        self._auth_token = None
        self._connected = False

    async def health(self) -> ConnectorStatus:
        """Return Zabbix API connector status."""
        return ConnectorStatus(
            name=self.display_name,
            enabled=self.enabled,
            connected=self.connected,
        )

    async def authenticate(self) -> str:
        """Authenticate and return a Zabbix API token."""
        result = await self._request(
            "user.login",
            {
                "username": self._settings.zabbix_username,
                "password": self._settings.zabbix_password,
            },
            authenticated=False,
        )
        return str(result)

    async def collect(self) -> list[dict[str, Any]]:
        """Collect raw Zabbix event data incrementally."""
        if not self.enabled or not self.connected:
            return []

        params: dict[str, Any] = {
            "output": "extend",
            "selectHosts": ["host", "name"],
            "sortfield": ["clock", "eventid"],
            "sortorder": "ASC",
            "limit": 100,
        }
        if self._last_event_clock is not None:
            params["time_from"] = self._last_event_clock + 1

        events = await self.event_get(params)
        normalized_events = [event for event in events if isinstance(event, dict)]
        clocks = [
            int(event["clock"])
            for event in normalized_events
            if str(event.get("clock", "")).isdigit()
        ]
        if clocks:
            self._last_event_clock = max(clocks)
        return normalized_events

    async def sync(self) -> list[ConnectorEvent]:
        """Collect and normalize Zabbix API events."""
        return [self.parse(payload) for payload in await self.collect()]

    def parse(self, payload: dict[str, Any]) -> ConnectorEvent:
        """Normalize one Zabbix API event payload."""
        clock = payload.get("clock")
        started_at = (
            datetime.fromtimestamp(int(clock), tz=UTC)
            if clock is not None and str(clock).isdigit()
            else None
        )
        hosts = payload.get("hosts") if isinstance(payload.get("hosts"), list) else []
        first_host = hosts[0] if hosts and isinstance(hosts[0], dict) else {}

        return ConnectorEvent(
            source=self.source,
            problem_id=str(payload.get("eventid")) if payload.get("eventid") else None,
            host=str(first_host.get("name") or first_host.get("host")) if first_host else None,
            severity=str(payload.get("severity")) if payload.get("severity") is not None else None,
            status=str(payload.get("value")) if payload.get("value") is not None else None,
            problem_name=str(payload.get("name")) if payload.get("name") else None,
            started_at=started_at,
            resolved_at=None,
            duration=None,
            raw_payload=payload,
        )

    async def event_get(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run Zabbix `event.get`."""
        return await self._list_request("event.get", params or {"output": "extend"})

    async def problem_get(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run Zabbix `problem.get`."""
        return await self._list_request("problem.get", params or {"output": "extend"})

    async def trigger_get(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run Zabbix `trigger.get`."""
        return await self._list_request("trigger.get", params or {"output": "extend"})

    async def host_get(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run Zabbix `host.get`."""
        return await self._list_request("host.get", params or {"output": "extend"})

    async def _list_request(self, method: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        result = await self._request(method, params, authenticated=True)
        if not isinstance(result, list):
            return []
        return [item for item in result if isinstance(item, dict)]

    async def _request(
        self,
        method: str,
        params: dict[str, Any],
        *,
        authenticated: bool,
    ) -> Any:
        if not self._client:
            raise RuntimeError("Zabbix API client is not initialized")

        body: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        if authenticated:
            body["auth"] = self._auth_token

        response = await self._client.post("", json=body)
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(f"Zabbix API error for {method}: {payload['error']}")
        return payload.get("result")
