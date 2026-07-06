"""Connector factory and registry."""

from collections.abc import Callable
from importlib import import_module

from app.connectors.base import BaseConnector
from app.connectors.discord import DiscordConnector
from app.connectors.zabbix_api import ZabbixApiConnector
from app.connectors.zabbix_database import ZabbixDatabaseConnector
from app.core.config.settings import Settings

ConnectorBuilder = Callable[[Settings], BaseConnector]
ConnectorClass = type[BaseConnector]


class ConnectorFactory:
    """Create connectors from a source registry."""

    def __init__(self) -> None:
        self._registry: dict[str, ConnectorBuilder] = {}

    def register(self, source: str, builder: ConnectorBuilder) -> None:
        """Register a connector builder."""
        self._registry[source] = builder

    def register_connector_class(self, connector_class: ConnectorClass) -> None:
        """Register a connector class by its source key."""
        self.register(connector_class.source, connector_class)

    def create(self, source: str, settings: Settings) -> BaseConnector:
        """Create a connector by source key."""
        try:
            return self._registry[source](settings)
        except KeyError as exc:
            raise ValueError(f"Unsupported connector source: {source}") from exc

    def registered_sources(self) -> tuple[str, ...]:
        """Return registered connector source keys."""
        return tuple(self._registry.keys())


def build_connector_factory() -> ConnectorFactory:
    """Build the default connector factory."""
    factory = ConnectorFactory()
    factory.register_connector_class(DiscordConnector)
    factory.register_connector_class(ZabbixApiConnector)
    factory.register_connector_class(ZabbixDatabaseConnector)
    return factory


def import_connector_class(import_path: str) -> ConnectorClass:
    """Import a connector class from a dotted import path."""
    module_path, _, class_name = import_path.strip().rpartition(".")
    if not module_path or not class_name:
        raise ValueError(f"Invalid connector import path: {import_path}")

    connector_class = getattr(import_module(module_path), class_name)
    if not isinstance(connector_class, type) or not issubclass(connector_class, BaseConnector):
        raise TypeError(f"Connector import must subclass BaseConnector: {import_path}")
    return connector_class
