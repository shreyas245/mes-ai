"""Master data ORM: materials, BOMs, products, routes, steps, step forms.

ISA-95 Part 2/4: material definition, product definition and segments.
Routes are **versioned** and move through Draft → Approved → Effective
(plan decision 6) so production always runs an approved version.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.shared.base_models import Entity


class MaterialDefinition(Entity):
    __tablename__ = "material_definition"

    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    uom: Mapped[str] = mapped_column(String(32), default="EA")
    is_lot_controlled: Mapped[bool] = mapped_column(default=True)


class BomItem(Entity):
    """A component line in a bill of materials (self-referencing for sub-BOMs)."""

    __tablename__ = "bom_item"

    parent_material_id: Mapped[str] = mapped_column(
        ForeignKey("material_definition.id"), index=True
    )
    component_material_id: Mapped[str] = mapped_column(
        ForeignKey("material_definition.id"), index=True
    )
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    uom: Mapped[str] = mapped_column(String(32), default="EA")


class Product(Entity):
    __tablename__ = "product"

    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    material_id: Mapped[str] = mapped_column(ForeignKey("material_definition.id"))


class RouteStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    EFFECTIVE = "effective"
    RETIRED = "retired"


class Route(Entity):
    """A versioned routing for a product."""

    __tablename__ = "route"
    __table_args__ = (UniqueConstraint("product_id", "version", name="uq_route_version"),)

    product_id: Mapped[str] = mapped_column(ForeignKey("product.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[RouteStatus] = mapped_column(
        SAEnum(RouteStatus), default=RouteStatus.DRAFT, index=True
    )


class RouteStep(Entity):
    __tablename__ = "route_step"

    route_id: Mapped[str] = mapped_column(ForeignKey("route.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    work_center_id: Mapped[str | None] = mapped_column(
        ForeignKey("plant_node.id"), default=None
    )


class StepForm(Entity):
    """Versioned JSON data-collection form attached to a route step.

    The form is JSON Schema; validation rules are a small DSL (see workflow).
    """

    __tablename__ = "step_form"

    route_step_id: Mapped[str] = mapped_column(ForeignKey("route_step.id"), index=True)
    schema_json: Mapped[str] = mapped_column(Text, default="{}")
    rules_json: Mapped[str] = mapped_column(Text, default="[]")
