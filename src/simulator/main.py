"""Run the simulator standalone (prints readings). Phase 3 will expose this over
an OPC UA server + MQTT so the edge gateway connects to it like a real line.
"""

from __future__ import annotations

import asyncio
import logging

from simulator.faults import Jam, MicroStop, SpeedLoss
from simulator.line import BottlingLine

logger = logging.getLogger(__name__)


async def run(cycles: int = 60, interval_s: float = 1.0) -> None:
    line = BottlingLine.default()
    # Inject representative faults onto the labeler (the usual trouble spot).
    line.stations[2].faults = [Jam(0.03), MicroStop(0.05), SpeedLoss(0.7, 0.1)]
    for _ in range(cycles):
        readings = line.readings()
        logger.info("%s", readings)
        await asyncio.sleep(interval_s)


def main() -> None:  # pragma: no cover - entry point
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())


if __name__ == "__main__":  # pragma: no cover
    main()
