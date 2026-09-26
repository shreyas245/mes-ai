"""Application configuration.

Pattern: **Singleton** (GoF, Creational).

`get_settings()` returns one cached `Settings` instance for the whole process.
We use `functools.lru_cache` rather than a hand-rolled singleton because it is
thread-safe, test-friendly (``get_settings.cache_clear()``) and idiomatic.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide settings, loaded from environment / ``.env``."""

    model_config = SettingsConfigDict(env_prefix="MES_", env_file=".env", extra="ignore")

    app_name: str = "mes-core"
    environment: str = "dev"
    debug: bool = True

    # Database — async SQLAlchemy URL. Defaults to local SQLite for zero-setup dev.
    database_url: str = "sqlite+aiosqlite:///./mes_core.db"

    # Event bus (NATS JetStream). When empty, the in-process bus is used.
    nats_url: str = ""

    # Audit hash chain seed (genesis hash).
    audit_genesis_hash: str = "0" * 64

    # Default site scope used when no auth context is present (dev only).
    default_site_id: str = "SITE-DEFAULT"


@lru_cache
def get_settings() -> Settings:
    """Return the single, cached :class:`Settings` instance (Singleton)."""
    return Settings()
