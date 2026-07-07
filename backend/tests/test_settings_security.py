"""Settings security validation tests."""

import pytest
from pydantic import ValidationError

from app.core.config.settings import Settings


def test_production_rejects_placeholder_secrets() -> None:
    """Production must not start with weak placeholder secrets."""
    with pytest.raises(ValidationError, match="Production requires secure values"):
        Settings(
            app_env="production",
            secret_key="change-me-with-a-secure-secret-key-32",
            postgres_password="alerthub_password",
            jwt_secret="change-me-with-a-secure-jwt-secret-32",
            discord_token="",
            discord_channel_id="",
        )


def test_production_accepts_secure_required_secrets() -> None:
    """Production settings accept non-placeholder secrets."""
    settings = Settings(
        app_env="production",
        secret_key="prod-secret-key-with-at-least-32-safe-chars",
        postgres_password="prod-postgres-password-with-entropy",
        jwt_secret="prod-jwt-secret-with-at-least-32-safe-chars",
        discord_token="discord-token-is-present",
        discord_channel_id="1234567890",
    )

    assert settings.is_production is True
