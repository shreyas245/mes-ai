"""Plant model ORM (ISA-95 Part 2 equipment hierarchy).

The hierarchy enterprise → site → area → line → work_center → equipment is stored
as a single self-referencing ``plant_node`` table with a ``level`` discriminator.
A unified tree is the natural fit for ISA-95 roles and lets the **Composite**
pattern (``composite.py``) treat any level uniformly for rollups.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mes_core.shared.base_models import Entity


class PlantLevel(str, enum.Enum):
    ENTERPRISE = "enterprise"
    SITE = "site"
    AREA = "area"
    LINE = "line"
    WORK_CENTER = "work_center"
    EQUIPMENT = "equipment"


class PlantNode(Entity):
    __tablename__ = "plant_node"

    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    level: Mapped[PlantLevel] = mapped_column(SAEnum(PlantLevel), index=True)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("plant_node.id"), default=None, index=True
    )

    children: Mapped[list["PlantNode"]] = relationship(
        backref="parent", remote_side="PlantNode.id", viewonly=True
    )


class TagMapping(Entity):
    """Maps a raw PLC/OPC-UA tag to an equipment node + a meaning."""

    __tablename__ = "tag_mapping"

    equipment_id: Mapped[str] = mapped_column(ForeignKey("plant_node.id"), index=True)
    tag_path: Mapped[str] = mapped_column(String(512), index=True)
    #: e.g. "good_count", "state", "speed", "temperature"
    meaning: Mapped[str] = mapped_column(String(64))
    unit: Mapped[str | None] = mapped_column(String(32), default=None)
