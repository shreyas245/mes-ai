"""Event-driven consumers (Observer).

The OEE/metrics engine reacts to production + machine events coming off the bus
instead of being called directly. This is where the modular monolith stays
decoupled: ``production`` emits, ``performance`` listens.
"""

from __future__ import annotations

import logging

from mes_core.production.events import OperationCompleted
from mes_core.shared.registry import on_event

logger = logging.getLogger(__name__)


@on_event(OperationCompleted.name)
async def on_operation_completed(event) -> None:
    """Placeholder consumer: a real engine would fold counts into the current
    OEE rollup window for the operation's work center."""
    logger.info(
        "OEE engine saw OperationCompleted good=%s scrap=%s",
        getattr(event, "good_count", None),
        getattr(event, "scrap_count", None),
    )
