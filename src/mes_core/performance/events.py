"""Performance domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mes_core.shared.events import DomainEvent, register_event


@register_event
@dataclass(frozen=True, slots=True)
class MachineStateChanged(DomainEvent):
    name: ClassVar[str] = "performance.machine_state_changed"
    equipment_id: str = ""
    state: str = ""


@register_event
@dataclass(frozen=True, slots=True)
class DowntimeReasonAssigned(DomainEvent):
    name: ClassVar[str] = "performance.downtime_reason_assigned"
    equipment_id: str = ""
    reason_code_id: str = ""
