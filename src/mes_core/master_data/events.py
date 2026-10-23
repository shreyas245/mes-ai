"""Master data domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mes_core.shared.events import DomainEvent, register_event


@register_event
@dataclass(frozen=True, slots=True)
class RouteApproved(DomainEvent):
    name: ClassVar[str] = "master_data.route_approved"
    product_id: str = ""
    version: int = 0
