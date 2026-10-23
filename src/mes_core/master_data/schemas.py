"""Master data API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from mes_core.master_data.models import RouteStatus


class MaterialCreate(BaseModel):
    code: str
    name: str
    uom: str = "EA"
    is_lot_controlled: bool = True


class MaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    name: str
    uom: str
    is_lot_controlled: bool


class ProductCreate(BaseModel):
    code: str
    name: str
    material_id: str


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    code: str
    name: str
    material_id: str


class RouteStepIn(BaseModel):
    name: str
    work_center_id: str | None = None
    form_schema_json: str = "{}"
    form_rules_json: str = "[]"


class RouteCreate(BaseModel):
    product_id: str
    version: int = 1
    steps: list[RouteStepIn] = []


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    version: int
    status: RouteStatus
