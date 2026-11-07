"""Quality domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mes_core.shared.events import DomainEvent, register_event


@register_event
@dataclass(frozen=True, slots=True)
class InspectionFailed(DomainEvent):
    name: ClassVar[str] = "quality.inspection_failed"
    plan_id: str = ""
    operation_id: str = ""
    lot_id: str = ""


@register_event
@dataclass(frozen=True, slots=True)
class LotPlacedOnHold(DomainEvent):
    name: ClassVar[str] = "quality.lot_on_hold"
    lot_id: str = ""
    reason: str = ""
