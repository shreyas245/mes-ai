"""Plant model domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mes_core.shared.events import DomainEvent, register_event


@register_event
@dataclass(frozen=True, slots=True)
class PlantNodeCreated(DomainEvent):
    name: ClassVar[str] = "plant.node_created"
    level: str = ""
    code: str = ""
