"""Application configuration backed by environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field, model_validator
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
    zabbix_web_url: str = ""
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
    sync_interval_seconds: int = Field(default=300, ge=60)
    enable_scheduled_report_delivery: bool = True
    weekly_report_interval_days: int = Field(default=7, ge=1)
    monthly_report_interval_days: int = Field(default=28, ge=7)
    default_escalation_owner: str = "NOC Team"
    escalation_owner_rules: str = (
        "disaster:Incident Manager;"
        "high:NOC Lead;"
        "average:NOC Operator;"
        "warning:NOC Operator;"
        "information:Monitoring Team"
    )
    auth_enabled: bool = True
    bootstrap_admin_email: str = "admin@alerthub.local"
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_password: str = Field(default="ChangeMeAdminPassword123!", min_length=12)

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        """Reject placeholder or missing secrets in production."""
        if not self.is_production:
            return self

        insecure_values = {
            "change-me-with-a-secure-secret-key-32",
            "change-me-with-a-secure-jwt-secret-32",
            "replace-with-a-secure-random-secret-key",
            "replace-with-a-secure-random-jwt-secret",
            "replace-with-a-secure-database-password",
            "replace-with-a-secure-admin-password",
            "ChangeMeAdminPassword123!",
            "alerthub_password",
        }
        required_secrets = {
            "SECRET_KEY": self.secret_key,
            "POSTGRES_PASSWORD": self.postgres_password,
            "JWT_SECRET": self.jwt_secret,
        }
        if self.auth_enabled:
            required_secrets["BOOTSTRAP_ADMIN_PASSWORD"] = self.bootstrap_admin_password
        if self.enable_discord:
            required_secrets["DISCORD_TOKEN"] = self.discord_token
            required_secrets["DISCORD_CHANNEL_ID"] = self.discord_channel_id

        invalid_names = [
            name
            for name, value in required_secrets.items()
            if not value or value in insecure_values
        ]
        if invalid_names:
            names = ", ".join(sorted(invalid_names))
            raise ValueError(f"Production requires secure values for: {names}")
        return self

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
