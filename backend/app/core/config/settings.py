"""Application configuration backed by environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for AlertHub Safe City."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AlertHub Safe City"
    app_env: Literal["local", "development", "staging", "production"] = "local"
    secret_key: str = Field(..., min_length=32)

    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "alerthub"
    postgres_user: str = "alerthub"
    postgres_password: str = Field(..., min_length=8)
    database_url: PostgresDsn | None = None

    event_source: str = "discord"
    connector_imports: str = ""
    enable_discord: bool = True
    enable_zabbix_api: bool = False
    enable_zabbix_db: bool = False

    discord_token: str = ""
    discord_guild_id: str = ""
    discord_channel_id: str = ""

    zabbix_api_url: str = ""
    zabbix_username: str = ""
    zabbix_password: str = ""

    zabbix_db_host: str = ""
    zabbix_db_port: int = 5432
    zabbix_db_name: str = ""
    zabbix_db_user: str = ""
    zabbix_db_password: str = ""

    jwt_secret: str = Field(..., min_length=32)
    jwt_expire_minutes: int = 60

    log_level: str = "INFO"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        """Build a PostgreSQL SQLAlchemy URL when DATABASE_URL is absent."""
        if self.database_url:
            return str(self.database_url)
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        """Return true when running in production."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
