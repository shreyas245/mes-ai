"""Edge gateway entry point.

Wires: connector (Factory) → tag map → state derivation (Strategy) →
store-and-forward publisher (Proxy). This is the one component that runs on the
plant floor, separate from mes-core (plan decision 1).
"""

from __future__ import annotations

import asyncio
import logging

from edge_gateway.buffer import LocalBuffer, Publisher, StoreAndForwardPublisher
from edge_gateway.config import get_edge_settings
from edge_gateway.connectors.factory import create_connector
from edge_gateway.state_derivation import SpeedRule, StateDeriver
from edge_gateway.tag_map import TagMap

logger = logging.getLogger(__name__)


class _LoggingPublisher(Publisher):
    """Placeholder target; replace with a NATS JetStream publisher."""

    async def publish(self, topic: str, payload: dict) -> None:
        logger.info("publish %s %s", topic, payload)


async def run_gateway(
    *, protocol: str, connector_config: dict, tag_map: TagMap,
    deriver: StateDeriver, publisher: Publisher | None = None,
) -> None:
    settings = get_edge_settings()
    connector = create_connector(protocol, connector_config)
    sink = StoreAndForwardPublisher(
        publisher or _LoggingPublisher(), LocalBuffer(settings.buffer_path)
    )

    await connector.connect()
    try:
        latest: dict[str, float | bool | str] = {}
        async for reading in connector.subscribe(tag_map.tags()):
            binding = tag_map.resolve(reading.tag_path)
            if binding is None:
                continue
            latest[binding.meaning] = reading.value
            await sink.publish(
                "mes.tag_value",
                {
                    "site_id": settings.site_id,
                    "equipment_id": binding.equipment_id,
                    "meaning": binding.meaning,
                    "value": reading.value,
                    "at": reading.at.isoformat(),
                },
            )
            state = deriver.derive(latest)
            await sink.publish(
                "mes.machine_state",
                {
                    "site_id": settings.site_id,
                    "equipment_id": binding.equipment_id,
                    "state": state.value,
                    "at": reading.at.isoformat(),
                },
            )
    finally:
        await connector.disconnect()


def main() -> None:  # pragma: no cover - entry point
    logging.basicConfig(level=logging.INFO)
    tag_map = TagMap()
    deriver = StateDeriver([SpeedRule(speed_tag="speed")])
    asyncio.run(
        run_gateway(
            protocol="opcua",
            connector_config={"endpoint": "opc.tcp://localhost:4840"},
            tag_map=tag_map,
            deriver=deriver,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
