"""Authentication and password security helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config.settings import get_settings

PASSWORD_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 password hash."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        f"{_b64encode(salt)}${_b64encode(digest)}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored PBKDF2 hash."""
    try:
        algorithm, iterations, salt, expected_digest = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _b64decode(salt),
            int(iterations),
        )
        return hmac.compare_digest(_b64encode(digest), expected_digest)
    except (ValueError, TypeError):
        return False


def create_access_token(
    *,
    subject: str,
    roles: list[str],
    permissions: list[str],
) -> str:
    """Create a signed bearer token."""
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": subject,
        "roles": roles,
        "permissions": permissions,
        "exp": int(expires_at.timestamp()),
        "iat": int(datetime.now(UTC).timestamp()),
    }
    payload_text = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _signature(payload_text, settings.jwt_secret)
    return f"{payload_text}.{signature}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a signed bearer token."""
    settings = get_settings()
    try:
        payload_text, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(_signature(payload_text, settings.jwt_secret), signature):
        return None
    try:
        payload = json.loads(_b64decode(payload_text))
    except (ValueError, TypeError):
        return None
    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        return None
    return payload if isinstance(payload, dict) else None


def _signature(payload_text: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload_text.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64encode(digest)


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
