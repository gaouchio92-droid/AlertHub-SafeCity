"""Zabbix API connector implementation."""

from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.connectors.base import BaseConnector, ConnectorEvent, ConnectorStatus
from app.core.config.settings import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SEVERITY_NAMES = {
    "0": "not_classified",
    "1": "information",
    "2": "warning",
    "3": "average",
    "4": "high",
    "5": "disaster",
}


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

        problem_params: dict[str, Any] = {
            "output": "extend",
            "selectAcknowledges": "extend",
            "selectHosts": ["hostid", "host", "name"],
            "selectTags": "extend",
            "recent": "true",
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "limit": 100,
        }
        event_params: dict[str, Any] = {
            "output": "extend",
            "selectHosts": ["hostid", "host", "name"],
            "selectRelatedObject": "extend",
            "select_acknowledges": "extend",
            "sortfield": ["clock", "eventid"],
            "sortorder": "ASC",
            "limit": 100,
        }
        if self._last_event_clock is not None:
            event_params["time_from"] = self._last_event_clock + 1

        problems = await self.problem_get(problem_params)
        events = await self.event_get(event_params)
        normalized_events = [
            {**event, "zabbix_payload_type": "event"}
            for event in events
            if isinstance(event, dict)
        ]
        normalized_events.extend(
            {**problem, "zabbix_payload_type": "problem"}
            for problem in problems
            if isinstance(problem, dict)
        )
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
        related_object = (
            payload.get("relatedObject")
            if isinstance(payload.get("relatedObject"), dict)
            else {}
        )
        problem_id = str(payload.get("eventid")) if payload.get("eventid") else None
        status = self._normalized_status(payload)
        severity = self._normalized_severity(payload.get("severity"))
        problem_name = str(
            payload.get("name")
            or related_object.get("description")
            or related_object.get("name")
            or ""
        ).strip() or None
        operational_data = self._operational_data(payload)
        links = self._event_links(problem_id, payload)

        return ConnectorEvent(
            source=self.source,
            problem_id=problem_id,
            host=str(first_host.get("name") or first_host.get("host")) if first_host else None,
            severity=severity,
            status=status,
            problem_name=problem_name,
            started_at=started_at,
            resolved_at=self._resolved_at(payload),
            duration=None,
            raw_payload={
                **payload,
                "normalized": {
                    "zabbix_problem_id": problem_id,
                    "status": status,
                    "host": str(first_host.get("name") or first_host.get("host"))
                    if first_host
                    else None,
                    "severity": severity,
                    "problem_name": problem_name,
                    "operational_data": operational_data,
                    "links": links,
                    "zabbix_payload_type": payload.get("zabbix_payload_type"),
                    "acknowledged": payload.get("acknowledged"),
                },
            },
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

    @staticmethod
    def _normalized_severity(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip().lower()
        return SEVERITY_NAMES.get(text, text.replace(" ", "_"))

    @staticmethod
    def _normalized_status(payload: dict[str, Any]) -> str:
        if payload.get("zabbix_payload_type") == "problem":
            return "problem"
        if str(payload.get("value")) == "1":
            return "problem"
        if str(payload.get("value")) == "0":
            return "resolved"
        if payload.get("r_eventid") not in (None, "0", 0):
            return "resolved"
        return "received"

    @staticmethod
    def _resolved_at(payload: dict[str, Any]) -> datetime | None:
        r_clock = payload.get("r_clock") or payload.get("rclock")
        if r_clock is None or not str(r_clock).isdigit() or int(r_clock) <= 0:
            return None
        return datetime.fromtimestamp(int(r_clock), tz=UTC)

    @staticmethod
    def _operational_data(payload: dict[str, Any]) -> str | None:
        for key in ("opdata", "operational_data", "description", "comments"):
            value = payload.get(key)
            if value:
                return str(value)
        related_object = payload.get("relatedObject")
        if isinstance(related_object, dict) and related_object.get("opdata"):
            return str(related_object["opdata"])
        return None

    def _event_links(self, problem_id: str | None, payload: dict[str, Any]) -> list[str]:
        web_url = self._zabbix_web_url()
        if not web_url:
            return []
        event_id = problem_id
        trigger_id = payload.get("objectid") or payload.get("triggerid")
        links: list[str] = []
        if trigger_id and event_id:
            links.append(f"{web_url}/tr_events.php?triggerid={trigger_id}&eventid={event_id}")
        elif event_id:
            links.append(f"{web_url}/zabbix.php?action=problem.view&eventids[]={event_id}")
        return links

    def _zabbix_web_url(self) -> str:
        if self._settings.zabbix_web_url:
            return self._settings.zabbix_web_url.rstrip("/")
        if not self._settings.zabbix_api_url:
            return ""
        parsed = urlparse(self._settings.zabbix_api_url)
        if not parsed.scheme or not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
