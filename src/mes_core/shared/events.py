"""Domain events and the event registry.

Patterns:
- **Prototype / value object** — events are immutable dataclasses.
- **Factory Method + Registry** — ``register_event`` / ``build_event`` rebuild a
  typed event from its stored name + payload (used by the outbox relay).

A domain event is a fact that already happened (past tense): ``OrderReleased``,
``OperationStarted``, ``MaterialConsumed`` (plan decision 4).
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, ClassVar


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base class for all domain events."""

    #: Stable topic name used on the bus and in the outbox.
    name: ClassVar[str] = "domain.event"

    aggregate_id: str
    site_id: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def payload(self) -> dict[str, Any]:
        """Serializable payload (datetimes → ISO strings)."""
        data = asdict(self)
        data["occurred_at"] = self.occurred_at.isoformat()
        return data


# --- registry (Factory Method) ------------------------------------------------

_REGISTRY: dict[str, type[DomainEvent]] = {}


def register_event(cls: type[DomainEvent]) -> type[DomainEvent]:
    """Class decorator: register an event type under its ``name``."""
    _REGISTRY[cls.name] = cls
    return cls


def build_event(name: str, payload: dict[str, Any]) -> DomainEvent:
    """Rebuild a typed event from a stored name + payload (Factory Method)."""
    cls = _REGISTRY.get(name, DomainEvent)
    data = dict(payload)
    if isinstance(data.get("occurred_at"), str):
        data["occurred_at"] = datetime.fromisoformat(data["occurred_at"])
    allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
    return cls(**{k: v for k, v in data.items() if k in allowed})
