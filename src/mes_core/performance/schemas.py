"""Performance API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReasonCodeCreate(BaseModel):
    code: str
    label: str
    parent_id: str | None = None


class MachineStateIn(BaseModel):
    equipment_id: str
    state: str


class OeeInputsIn(BaseModel):
    equipment_id: str
    planned_time_s: float
    run_time_s: float
    ideal_cycle_time_s: float
    total_count: float
    good_count: float


class OeeRollupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    equipment_id: str
    window_start: datetime
    availability: float
    performance: float
    quality: float
    oee: float
