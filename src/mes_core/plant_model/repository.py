"""Plant model repositories."""

from __future__ import annotations

from mes_core.plant_model.models import PlantNode, TagMapping
from mes_core.shared.repository import SqlAlchemyRepository


class PlantNodeRepository(SqlAlchemyRepository[PlantNode]):
    model = PlantNode


class TagMappingRepository(SqlAlchemyRepository[TagMapping]):
    model = TagMapping
