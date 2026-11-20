"""Protocol connector interface + the reading value object.

The edge gateway talks to machines over several protocols (OPC UA, MQTT Sparkplug
B, Modbus). They share one interface so the rest of the gateway is
protocol-agnostic (see ``factory.py`` for the Abstract Factory that builds them).
"""

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class TagReading:
    tag_path: str
    value: float | bool | str
    at: datetime

    @staticmethod
    def now(tag_path: str, value: float | bool | str) -> "TagReading":
        return TagReading(tag_path, value, datetime.now(timezone.utc))


class Connector(abc.ABC):
    """A source of tag readings."""

    @abc.abstractmethod
    async def connect(self) -> None: ...

    @abc.abstractmethod
    async def disconnect(self) -> None: ...

    @abc.abstractmethod
    def subscribe(self, tag_paths: list[str]) -> AsyncIterator[TagReading]: ...
