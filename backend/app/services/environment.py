"""Safe environment file management for connector settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.core.config.settings import get_settings

ENV_PATH = Path(os.getenv("ALERTHUB_ENV_FILE", "/app/.env"))
SECRET_KEYS = {
    "DISCORD_TOKEN",
    "ZABBIX_PASSWORD",
    "ZABBIX_DB_PASSWORD",
}
CONNECTOR_ENV_KEYS = [
    "EVENT_SOURCE",
    "ENABLE_DISCORD",
    "ENABLE_ZABBIX_API",
    "ENABLE_ZABBIX_DB",
    "DISCORD_TOKEN",
    "DISCORD_GUILD_ID",
    "DISCORD_CHANNEL_ID",
    "ZABBIX_API_URL",
    "ZABBIX_WEB_URL",
    "ZABBIX_USERNAME",
    "ZABBIX_PASSWORD",
    "ZABBIX_DB_HOST",
    "ZABBIX_DB_PORT",
    "ZABBIX_DB_NAME",
    "ZABBIX_DB_USER",
    "ZABBIX_DB_PASSWORD",
]


@dataclass(frozen=True)
class EnvironmentValue:
    """One sanitized environment value."""

    key: str
    value: str
    secret: bool
    configured: bool


class ConnectorEnvironmentService:
    """Read and update allowed connector environment variables."""

    def __init__(self, env_path: Path = ENV_PATH) -> None:
        self._env_path = env_path

    def values(self) -> list[EnvironmentValue]:
        """Return connector settings without exposing secret values."""
        data = self._read_env()
        values: list[EnvironmentValue] = []
        for key in CONNECTOR_ENV_KEYS:
            value = data.get(key, "")
            secret = key in SECRET_KEYS
            values.append(
                EnvironmentValue(
                    key=key,
                    value="********" if secret and value else value,
                    secret=secret,
                    configured=bool(value),
                )
            )
        return values

    def update(self, updates: dict[str, str]) -> list[EnvironmentValue]:
        """Persist allowed connector settings to the mounted .env file."""
        invalid_keys = sorted(set(updates) - set(CONNECTOR_ENV_KEYS))
        if invalid_keys:
            names = ", ".join(invalid_keys)
            raise ValueError(f"Unsupported connector environment keys: {names}")

        data = self._read_env()
        for key, raw_value in updates.items():
            value = raw_value.strip()
            if key in SECRET_KEYS and value == "********":
                continue
            data[key] = value
            os.environ[key] = value

        self._write_env(data)
        get_settings.cache_clear()
        return self.values()

    def _read_env(self) -> dict[str, str]:
        if not self._env_path.exists():
            return {}

        data: dict[str, str] = {}
        for line in self._env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            data[key.strip()] = _unquote(value.strip())
        return data

    def _write_env(self, data: dict[str, str]) -> None:
        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        existing_lines = (
            self._env_path.read_text(encoding="utf-8").splitlines()
            if self._env_path.exists()
            else []
        )
        emitted_keys: set[str] = set()
        lines: list[str] = []

        for line in existing_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                lines.append(line)
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in data:
                lines.append(f"{key}={_quote(data[key])}")
                emitted_keys.add(key)
            else:
                lines.append(line)

        for key in CONNECTOR_ENV_KEYS:
            if key in data and key not in emitted_keys:
                lines.append(f"{key}={_quote(data[key])}")

        self._env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _quote(value: str) -> str:
    if value == "":
        return ""
    if any(character.isspace() for character in value) or any(
        character in value for character in ['"', "#", ";"]
    ):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value
