"""Event bus — how domain events reach consumers.

Patterns:
- **Observer** — subscribers register for event names and are notified.
- **Mediator** — the bus decouples publishers (modules) from consumers
  (OEE engine, reporting, integrations, copilot). Modules never call each other.
- **Strategy** — the transport (in-process now, NATS JetStream later) is a
  pluggable strategy behind one ``EventBus`` interface.
- **Proxy** — ``BufferedBusProxy`` adds store-and-forward in front of a real bus
  (used on the edge; see also ``edge_gateway.buffer``).
"""

from __future__ import annotations

import abc
import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable

from mes_core.shared.events import DomainEvent

logger = logging.getLogger(__name__)

Handler = Callable[[DomainEvent], Awaitable[None]]


class EventBus(abc.ABC):
    """Abstract transport (Strategy)."""

    @abc.abstractmethod
    def subscribe(self, event_name: str, handler: Handler) -> None: ...

    @abc.abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...


class InProcessEventBus(EventBus):
    """Synchronous-dispatch in-process bus (Observer).

    Good for the modular monolith and tests; a NATS-backed bus implements the
    same interface for cross-process delivery.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._subscribers[event_name].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = list(self._subscribers.get(event.name, ()))
        if not handlers:
            return
        results = await asyncio.gather(
            *(h(event) for h in handlers), return_exceptions=True
        )
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.exception(
                    "subscriber %s failed for %s", handler, event.name,
                    exc_info=result,
                )


class BufferedBusProxy(EventBus):
    """Store-and-forward proxy (Proxy pattern).

    Delegates to a real bus; if publishing fails (network down), events are
    queued and replayed in order on the next successful publish or ``flush``.
    """

    def __init__(self, target: EventBus) -> None:
        self._target = target
        self._buffer: list[DomainEvent] = []

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._target.subscribe(event_name, handler)

    async def publish(self, event: DomainEvent) -> None:
        self._buffer.append(event)
        await self.flush()

    async def flush(self) -> None:
        while self._buffer:
            event = self._buffer[0]
            try:
                await self._target.publish(event)
            except Exception:  # keep order; retry later
                logger.warning("bus unavailable, buffered %s", event.name)
                return
            self._buffer.pop(0)


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Return the process event bus (lazy Singleton)."""
    global _bus
    if _bus is None:
        _bus = InProcessEventBus()
    return _bus


def set_event_bus(bus: EventBus) -> None:
    """Swap the bus (tests / NATS wiring)."""
    global _bus
    _bus = bus
