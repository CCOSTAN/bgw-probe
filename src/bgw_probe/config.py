"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlparse


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    value = int(os.getenv(name, str(default)))
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def normalize_gateway_url(value: str) -> str:
    url = value.strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("BGW_URL must be an http or https URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("BGW_URL must not contain credentials, a query, or a fragment")
    if parsed.path not in {"", "/"}:
        raise ValueError("BGW_URL must point to the gateway root")
    return url


@dataclass(frozen=True)
class Settings:
    gateway_url: str
    timeout_seconds: int
    poll_interval_seconds: int
    tls_verify: bool
    bind: str
    port: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            gateway_url=normalize_gateway_url(
                os.getenv("BGW_URL", "https://192.168.1.254")
            ),
            timeout_seconds=_env_int("BGW_TIMEOUT_SECONDS", 8, 1, 30),
            poll_interval_seconds=_env_int(
                "BGW_POLL_INTERVAL_SECONDS", 60, 15, 3600
            ),
            tls_verify=_env_bool("BGW_TLS_VERIFY", False),
            bind=os.getenv("BGW_BIND", "0.0.0.0").strip(),
            port=_env_int("BGW_PORT", 8080, 1, 65535),
        )
