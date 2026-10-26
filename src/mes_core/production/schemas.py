"""Production API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from mes_core.production.states import OperationState, OrderState


class OrderCreate(BaseModel):
    order_no: str
    product_id: str
    route_id: str
    quantity: float
    line_id: str | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_no: str
    product_id: str
    route_id: str
    line_id: str | None
    quantity: float
    state: OrderState


class OperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_id: str
    sequence: int
    work_center_id: str | None
    state: OperationState
    good_count: float
    scrap_count: float


class CompletePayload(BaseModel):
    good_count: float
    scrap_count: float = 0.0


class ConsumePayload(BaseModel):
    lot_id: str
    quantity: float
