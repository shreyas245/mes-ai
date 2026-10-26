"""Production ORM (ISA-95 operations request/schedule + performance).

production_order ─< order_operation ─< operation_execution
                                        ├─< material_consumption
                                        ├─< production_output
                                        └─< data_collection_value
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.production.states import OperationState, OrderState
from mes_core.shared.base_models import Entity


class ProductionOrder(Entity):
    __tablename__ = "production_order"

    order_no: Mapped[str] = mapped_column(String(64), index=True)
    product_id: Mapped[str] = mapped_column(String(36), index=True)
    route_id: Mapped[str] = mapped_column(String(36))
    line_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[OrderState] = mapped_column(
        SAEnum(OrderState), default=OrderState.CREATED, index=True
    )


class OrderOperation(Entity):
    __tablename__ = "order_operation"

    order_id: Mapped[str] = mapped_column(ForeignKey("production_order.id"), index=True)
    route_step_id: Mapped[str] = mapped_column(String(36))
    sequence: Mapped[int] = mapped_column(Integer)
    work_center_id: Mapped[str | None] = mapped_column(String(36), default=None, index=True)
    state: Mapped[OperationState] = mapped_column(
        SAEnum(OperationState), default=OperationState.PENDING, index=True
    )
    good_count: Mapped[float] = mapped_column(Float, default=0.0)
    scrap_count: Mapped[float] = mapped_column(Float, default=0.0)


class OperationExecution(Entity):
    __tablename__ = "operation_execution"

    operation_id: Mapped[str] = mapped_column(ForeignKey("order_operation.id"), index=True)
    operator: Mapped[str] = mapped_column(String(128))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class MaterialConsumption(Entity):
    __tablename__ = "material_consumption"

    operation_id: Mapped[str] = mapped_column(ForeignKey("order_operation.id"), index=True)
    lot_id: Mapped[str] = mapped_column(String(36), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)


class ProductionOutput(Entity):
    __tablename__ = "production_output"

    operation_id: Mapped[str] = mapped_column(ForeignKey("order_operation.id"), index=True)
    lot_id: Mapped[str] = mapped_column(String(36), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)


class DataCollectionValue(Entity):
    __tablename__ = "data_collection_value"

    operation_id: Mapped[str] = mapped_column(ForeignKey("order_operation.id"), index=True)
    field_key: Mapped[str] = mapped_column(String(128))
    value_json: Mapped[str] = mapped_column(Text, default="null")
