"""Production domain events (plan decision 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mes_core.shared.events import DomainEvent, register_event


@register_event
@dataclass(frozen=True, slots=True)
class OrderReleased(DomainEvent):
    name: ClassVar[str] = "production.order_released"
    order_no: str = ""
    line_id: str = ""


@register_event
@dataclass(frozen=True, slots=True)
class OperationStarted(DomainEvent):
    name: ClassVar[str] = "production.operation_started"
    order_id: str = ""
    work_center_id: str = ""


@register_event
@dataclass(frozen=True, slots=True)
class OperationCompleted(DomainEvent):
    name: ClassVar[str] = "production.operation_completed"
    order_id: str = ""
    good_count: float = 0.0
    scrap_count: float = 0.0


@register_event
@dataclass(frozen=True, slots=True)
class MaterialConsumed(DomainEvent):
    name: ClassVar[str] = "production.material_consumed"
    operation_id: str = ""
    lot_id: str = ""
    quantity: float = 0.0
