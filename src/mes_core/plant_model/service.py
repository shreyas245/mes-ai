"""Plant model service (module Facade).

Owns ``plant_node`` + ``tag_mapping``. Other modules reach plant data only
through this service, never by querying the tables directly.
"""

from __future__ import annotations

from mes_core.plant_model.composite import PlantTreeNode, build_tree
from mes_core.plant_model.events import PlantNodeCreated
from mes_core.plant_model.models import PlantNode, TagMapping
from mes_core.plant_model.repository import PlantNodeRepository, TagMappingRepository
from mes_core.plant_model.schemas import PlantNodeCreate
from mes_core.shared.context import OperationContext
from mes_core.shared.rbac import authorize
from mes_core.shared.service import DomainService


class PlantModelService(DomainService):
    @property
    def nodes(self) -> PlantNodeRepository:
        return PlantNodeRepository(self.session)

    @property
    def tags(self) -> TagMappingRepository:
        return TagMappingRepository(self.session)

    async def create_node(
        self, ctx: OperationContext, data: PlantNodeCreate
    ) -> PlantNode:
        authorize(ctx, ctx.site_id, required_role="engineer")
        node = PlantNode(
            site_id=ctx.site_id,
            code=data.code,
            name=data.name,
            level=data.level,
            parent_id=data.parent_id,
        )
        self.nodes.add(node)
        await self.session.flush()
        await self._record(
            ctx,
            action="create",
            entity_type="plant_node",
            entity_id=node.id,
            new_values={"code": node.code, "level": node.level.value},
            event=PlantNodeCreated(
                aggregate_id=node.id,
                site_id=ctx.site_id,
                level=node.level.value,
                code=node.code,
            ),
        )
        return node

    async def get_tree(self, ctx: OperationContext) -> list[PlantTreeNode]:
        rows = await self.nodes.list(site_id=ctx.site_id, limit=10_000)
        return build_tree(rows)

    async def map_tag(
        self, ctx: OperationContext, *, equipment_id: str, tag_path: str,
        meaning: str, unit: str | None = None,
    ) -> TagMapping:
        authorize(ctx, ctx.site_id, required_role="engineer")
        mapping = TagMapping(
            site_id=ctx.site_id,
            equipment_id=equipment_id,
            tag_path=tag_path,
            meaning=meaning,
            unit=unit,
        )
        self.tags.add(mapping)
        await self.session.flush()
        return mapping
