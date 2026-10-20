"""Plant model API schemas (Pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from mes_core.plant_model.models import PlantLevel


class PlantNodeCreate(BaseModel):
    code: str
    name: str
    level: PlantLevel
    parent_id: str | None = None


class PlantNodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    level: PlantLevel
    parent_id: str | None
    site_id: str


class PlantTreeOut(BaseModel):
    id: str
    code: str
    name: str
    level: PlantLevel
    children: list["PlantTreeOut"] = []
