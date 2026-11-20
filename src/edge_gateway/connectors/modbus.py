"""Modbus connector (scaffold)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from edge_gateway.connectors.base import Connector, TagReading


class ModbusConnector(Connector):
    def __init__(self, host: str, port: int = 502) -> None:
        self.host = host
        self.port = port

    async def connect(self) -> None:  # pragma: no cover - scaffold
        ...

    async def disconnect(self) -> None:  # pragma: no cover - scaffold
        ...

    async def subscribe(self, tag_paths: list[str]) -> AsyncIterator[TagReading]:
        if False:  # pragma: no cover - scaffold yields nothing yet
            yield TagReading.now("", 0)
        return
