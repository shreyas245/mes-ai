"""Genealogy domain events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mes_core.shared.events import DomainEvent, register_event


@register_event
@dataclass(frozen=True, slots=True)
class LotProduced(DomainEvent):
    name: ClassVar[str] = "genealogy.lot_produced"
    lot_code: str = ""
    material_id: str = ""


@register_event
@dataclass(frozen=True, slots=True)
class GenealogyLinked(DomainEvent):
    name: ClassVar[str] = "genealogy.linked"
    parent_lot_id: str = ""
    child_lot_id: str = ""
