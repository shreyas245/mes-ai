"""Module registry (Mediator-style wiring).

Modules register their event subscriptions here at startup so the app can wire
the bus without any module importing another. The app factory calls
``install_subscribers`` once.
"""

from __future__ import annotations

from collections.abc import Callable

from mes_core.shared.event_bus import EventBus, get_event_bus

#: list of (event_name, handler) declared by modules at import time.
_SUBSCRIPTIONS: list[tuple[str, Callable]] = []


def on_event(event_name: str):
    """Decorator used by modules to declare an async event handler."""

    def wrap(handler: Callable) -> Callable:
        _SUBSCRIPTIONS.append((event_name, handler))
        return handler

    return wrap


def install_subscribers(bus: EventBus | None = None) -> int:
    bus = bus or get_event_bus()
    for name, handler in _SUBSCRIPTIONS:
        bus.subscribe(name, handler)
    return len(_SUBSCRIPTIONS)
