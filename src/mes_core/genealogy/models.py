"""Genealogy ORM: material lots and parent→child genealogy links.

Genealogy owns ``material_lot`` and ``genealogy_link``. Production references
lots by id but never queries these tables directly (module boundary).
"""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.shared.base_models import Entity


class MaterialLot(Entity):
    __tablename__ = "material_lot"

    lot_code: Mapped[str] = mapped_column(String(64), index=True)
    material_id: Mapped[str] = mapped_column(String(36), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    uom: Mapped[str] = mapped_column(String(32), default="EA")
    #: serial number when the lot represents a single serialized unit.
    serial: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    status: Mapped[str] = mapped_column(String(32), default="available")


class GenealogyLink(Entity):
    """A consumed (parent) lot contributing to a produced (child) lot."""

    __tablename__ = "genealogy_link"

    parent_lot_id: Mapped[str] = mapped_column(ForeignKey("material_lot.id"), index=True)
    child_lot_id: Mapped[str] = mapped_column(ForeignKey("material_lot.id"), index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
