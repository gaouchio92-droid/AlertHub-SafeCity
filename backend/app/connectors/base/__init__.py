"""Base connector contracts."""

from app.connectors.base.connector import BaseConnector
from app.connectors.base.event import ConnectorEvent
from app.connectors.base.status import ConnectorStatus

__all__ = ["BaseConnector", "ConnectorEvent", "ConnectorStatus"]
