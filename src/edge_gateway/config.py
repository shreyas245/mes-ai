"""Edge gateway configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class EdgeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EDGE_", env_file=".env", extra="ignore")

    site_id: str = "SITE-DEFAULT"
    line_id: str = "LINE-1"
    nats_url: str = "nats://localhost:4222"
    buffer_path: str = "edge_buffer.db"
    poll_interval_s: float = 1.0


@lru_cache
def get_edge_settings() -> EdgeSettings:
    return EdgeSettings()
