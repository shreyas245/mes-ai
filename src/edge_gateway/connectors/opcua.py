"""OPC UA connector (uses ``asyncua`` in production).

Kept import-light: the heavy ``asyncua`` dependency is imported lazily inside
``connect`` so the module loads without the optional ``edge`` extra installed.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from edge_gateway.connectors.base import Connector, TagReading


class OpcUaConnector(Connector):
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self._client = None

    async def connect(self) -> None:
        from asyncua import Client  # lazy import (optional dependency)

        self._client = Client(url=self.endpoint)
        await self._client.connect()

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    async def subscribe(self, tag_paths: list[str]) -> AsyncIterator[TagReading]:
        if self._client is None:
            raise RuntimeError("connect() first")
        # Minimal polling read; a real impl uses OPC UA subscriptions.
        for path in tag_paths:
            node = self._client.get_node(path)
            value = await node.read_value()
            yield TagReading.now(path, value)
