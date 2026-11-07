"""Quality ORM: inspection plans, characteristics, results, nonconformances."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.shared.base_models import Entity


class InspectionPlan(Entity):
    __tablename__ = "inspection_plan"

    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    route_step_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    #: if True, a failed in-process check blocks the operation.
    blocking: Mapped[bool] = mapped_column(Boolean, default=True)


class Characteristic(Entity):
    __tablename__ = "characteristic"

    plan_id: Mapped[str] = mapped_column(ForeignKey("inspection_plan.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    lower_limit: Mapped[float | None] = mapped_column(Float, default=None)
    upper_limit: Mapped[float | None] = mapped_column(Float, default=None)
    unit: Mapped[str | None] = mapped_column(String(32), default=None)


class InspectionResult(Entity):
    __tablename__ = "inspection_result"

    plan_id: Mapped[str] = mapped_column(ForeignKey("inspection_plan.id"), index=True)
    operation_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    lot_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=True)


class Measurement(Entity):
    __tablename__ = "measurement"

    result_id: Mapped[str] = mapped_column(ForeignKey("inspection_result.id"), index=True)
    characteristic_id: Mapped[str] = mapped_column(ForeignKey("characteristic.id"))
    value: Mapped[float | None] = mapped_column(Float, default=None)
    in_spec: Mapped[bool] = mapped_column(Boolean, default=True)


class Nonconformance(Entity):
    __tablename__ = "nonconformance"

    lot_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    description: Mapped[str] = mapped_column(String(1024), default="")
    status: Mapped[str] = mapped_column(String(32), default="open")  # open/hold/released
