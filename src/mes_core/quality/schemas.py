"""Quality API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class PlanCreate(BaseModel):
    code: str
    name: str
    route_step_id: str | None = None
    blocking: bool = True


class CharacteristicCreate(BaseModel):
    plan_id: str
    name: str
    lower_limit: float | None = None
    upper_limit: float | None = None
    unit: str | None = None


class MeasurementIn(BaseModel):
    characteristic: str
    value: float | None
    lower: float | None = None
    upper: float | None = None


class InProcessCheck(BaseModel):
    plan_id: str
    operation_id: str
    lot_id: str
    measurements: list[MeasurementIn]
