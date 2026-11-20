"""MQTT Sparkplug B connector (uses ``paho-mqtt`` in production).

Simplified: subscribes to Sparkplug topics and yields decoded metric readings.
The protobuf decode is omitted here; the shape of the connector is the point.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from edge_gateway.connectors.base import Connector, TagReading


class MqttSparkplugConnector(Connector):
    def __init__(self, broker: str, group_id: str) -> None:
        self.broker = broker
        self.group_id = group_id
        self._queue: asyncio.Queue[TagReading] = asyncio.Queue()
        self._client = None

    async def connect(self) -> None:
        import paho.mqtt.client as mqtt  # lazy import (optional dependency)

        self._client = mqtt.Client()
        self._client.connect_async(self.broker)
        self._client.loop_start()

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client = None

    async def subscribe(self, tag_paths: list[str]) -> AsyncIterator[TagReading]:
        # In production, on_message decodes Sparkplug payloads into the queue.
        while True:
            reading = await self._queue.get()
            yield reading
