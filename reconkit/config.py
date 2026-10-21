"""Configuration for ReconKit.

Loads settings from environment variables (and an optional ``.env`` file)
plus an optional YAML config file. Everything has a sensible default so the
tool runs out of the box with zero configuration.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, populated from env vars prefixed with ``RECONKIT_``
    plus bare API-key vars (e.g. ``SHODAN_API_KEY``)."""

    model_config = SettingsConfigDict(
        env_prefix="RECONKIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core
    database_url: str = "sqlite+aiosqlite:///./data/reconkit.db"
    secret_key: str = "dev-insecure-secret-change-me"
    max_concurrency: int = 5
    default_timeout: int = 120

    # Cache
    cache_backend: str = "disk"  # disk | redis | none
    cache_ttl: int = 86400
    cache_dir: str = "./data/cache"
    redis_url: str = "redis://localhost:6379/0"

    # Web auth bootstrap
    admin_user: str = "admin"
    admin_password: str = "changeme"
    jwt_expire_minutes: int = 720
    require_auth: bool = False  # when False, API is open (single-user local use)
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Optional API keys (read from bare env vars, not prefixed)
    shodan_api_key: str = Field(default="", validation_alias="SHODAN_API_KEY")
    virustotal_api_key: str = Field(default="", validation_alias="VIRUSTOTAL_API_KEY")
    abuseipdb_api_key: str = Field(default="", validation_alias="ABUSEIPDB_API_KEY")
    hunter_api_key: str = Field(default="", validation_alias="HUNTER_API_KEY")
    otx_api_key: str = Field(default="", validation_alias="OTX_API_KEY")
    github_token: str = Field(default="", validation_alias="GITHUB_TOKEN")
    google_cse_api_key: str = Field(default="", validation_alias="GOOGLE_CSE_API_KEY")
    google_cse_id: str = Field(default="", validation_alias="GOOGLE_CSE_ID")
    ipinfo_token: str = Field(default="", validation_alias="IPINFO_TOKEN")

    # Per-source rate limits (seconds between requests), overridable via YAML
    rate_limits: dict[str, float] = Field(default_factory=dict)

    def api_key_for(self, service: str) -> str:
        """Return the configured key for a service name, or empty string."""
        return str(getattr(self, f"{service}_api_key", "") or getattr(self, f"{service}_token", "") or "")

    def has_key(self, service: str) -> bool:
        return bool(self.api_key_for(service))

    def data_path(self) -> Path:
        # Derive a data dir from the sqlite URL when possible, else ./data
        p = Path("./data")
        p.mkdir(parents=True, exist_ok=True)
        return p


def _load_yaml(path: str | os.PathLike[str]) -> dict[str, Any]:
    file = Path(path)
    if not file.exists():
        return {}
    with file.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def get_settings(config_file: str | None = None) -> Settings:
    """Return a cached Settings instance.

    If a YAML config file is present (``reconkit.yml`` by default) its values
    are merged in as a base layer; environment variables still take priority.
    """
    yaml_path = config_file or os.environ.get("RECONKIT_CONFIG", "reconkit.yml")
    base = _load_yaml(yaml_path)
    settings = Settings(**base)
    # Ensure cache + data dirs exist
    Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
    settings.data_path()
    return settings
