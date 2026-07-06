"""Zabbix database connector implementation."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.connectors.base import BaseConnector, ConnectorEvent, ConnectorStatus
from app.core.config.settings import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ZabbixDatabaseConnector(BaseConnector):
    """Optional read-only connector for Zabbix PostgreSQL event data."""

    source = "zabbix_database"
    display_name = "Zabbix Database"

    def __init__(self, settings: Settings) -> None:
        super().__init__(enabled=settings.enable_zabbix_db)
        self._settings = settings
        self._engine: Engine | None = None
        self._last_event_id: int | None = None

    async def connect(self) -> None:
        """Initialize a read-only Zabbix database engine."""
        if not self.enabled:
            return
        if not (
            self._settings.zabbix_db_host
            and self._settings.zabbix_db_name
            and self._settings.zabbix_db_user
            and self._settings.zabbix_db_password
        ):
            logger.warning("Zabbix database connector enabled but missing credentials")
            return

        self._engine = create_engine(self._database_uri, pool_pre_ping=True)
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        self._connected = True

    async def disconnect(self) -> None:
        """Dispose Zabbix database resources."""
        if self._engine:
            self._engine.dispose()
        self._engine = None
        self._connected = False

    async def health(self) -> ConnectorStatus:
        """Return Zabbix database connector status."""
        return ConnectorStatus(
            name=self.display_name,
            enabled=self.enabled,
            connected=self.connected,
        )

    async def collect(self) -> list[dict[str, Any]]:
        """Read Zabbix events incrementally without modifying the Zabbix database."""
        if not self.enabled or not self.connected or not self._engine:
            return []

        query = """
            SELECT eventid, clock, name, severity, value
            FROM events
            WHERE (:last_event_id IS NULL OR eventid > :last_event_id)
            ORDER BY eventid ASC
            LIMIT 100
        """
        with self._engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            rows = connection.execute(
                text(query),
                {"last_event_id": self._last_event_id},
            ).mappings().all()

        payloads = [dict(row) for row in rows]
        ids = [int(row["eventid"]) for row in payloads if row.get("eventid") is not None]
        if ids:
            self._last_event_id = max(ids)
        return payloads

    async def sync(self) -> list[ConnectorEvent]:
        """Collect and normalize Zabbix database events."""
        return [self.parse(payload) for payload in await self.collect()]

    def parse(self, payload: dict[str, Any]) -> ConnectorEvent:
        """Normalize one Zabbix database event row."""
        clock = payload.get("clock")
        started_at = (
            datetime.fromtimestamp(int(clock), tz=UTC)
            if clock is not None and str(clock).isdigit()
            else None
        )
        return ConnectorEvent(
            source=self.source,
            problem_id=str(payload.get("eventid")) if payload.get("eventid") else None,
            host=None,
            severity=str(payload.get("severity")) if payload.get("severity") is not None else None,
            status=str(payload.get("value")) if payload.get("value") is not None else None,
            problem_name=str(payload.get("name")) if payload.get("name") else None,
            started_at=started_at,
            resolved_at=None,
            duration=None,
            raw_payload=payload,
        )

    @property
    def _database_uri(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self._settings.zabbix_db_user}:{self._settings.zabbix_db_password}"
            f"@{self._settings.zabbix_db_host}:{self._settings.zabbix_db_port}"
            f"/{self._settings.zabbix_db_name}"
        )
