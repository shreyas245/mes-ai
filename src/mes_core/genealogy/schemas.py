"""Genealogy API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LotCreate(BaseModel):
    lot_code: str
    material_id: str
    quantity: float
    uom: str = "EA"
    serial: str | None = None


class LotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    lot_code: str
    material_id: str
    quantity: float
    uom: str
    serial: str | None
    status: str


class TraceRow(BaseModel):
    depth: int
    lot_code: str
