"""Master data service (module Facade).

Owns materials, BOMs, products, routes, steps and forms.
"""

from __future__ import annotations

from mes_core.master_data.builder import RouteBuilder
from mes_core.master_data.events import RouteApproved
from mes_core.master_data.models import (
    MaterialDefinition,
    Product,
    Route,
    RouteStatus,
)
from mes_core.master_data.repository import (
    MaterialRepository,
    ProductRepository,
    RouteRepository,
)
from mes_core.master_data.schemas import MaterialCreate, ProductCreate, RouteCreate
from mes_core.shared.context import OperationContext
from mes_core.shared.rbac import authorize
from mes_core.shared.service import DomainService


class MasterDataService(DomainService):
    async def create_material(
        self, ctx: OperationContext, data: MaterialCreate
    ) -> MaterialDefinition:
        authorize(ctx, ctx.site_id, required_role="engineer")
        material = MaterialDefinition(site_id=ctx.site_id, **data.model_dump())
        MaterialRepository(self.session).add(material)
        await self.session.flush()
        await self._record(
            ctx, action="create", entity_type="material_definition",
            entity_id=material.id, new_values={"code": material.code},
        )
        return material

    async def create_product(
        self, ctx: OperationContext, data: ProductCreate
    ) -> Product:
        authorize(ctx, ctx.site_id, required_role="engineer")
        product = Product(site_id=ctx.site_id, **data.model_dump())
        ProductRepository(self.session).add(product)
        await self.session.flush()
        await self._record(
            ctx, action="create", entity_type="product",
            entity_id=product.id, new_values={"code": product.code},
        )
        return product

    async def create_route(self, ctx: OperationContext, data: RouteCreate) -> Route:
        authorize(ctx, ctx.site_id, required_role="engineer")
        builder = RouteBuilder(
            site_id=ctx.site_id, product_id=data.product_id, version=data.version
        )
        for step in data.steps:
            builder.step(
                name=step.name,
                work_center_id=step.work_center_id,
                schema_json=step.form_schema_json,
                rules_json=step.form_rules_json,
            )
        draft = builder.build()
        self.session.add(draft.route)
        self.session.add_all(draft.steps)
        self.session.add_all(draft.forms)
        await self.session.flush()
        await self._record(
            ctx, action="create", entity_type="route", entity_id=draft.route.id,
            new_values={"version": draft.route.version, "steps": len(draft.steps)},
        )
        return draft.route

    async def approve_route(self, ctx: OperationContext, route_id: str) -> Route:
        authorize(ctx, ctx.site_id, required_role="engineer")
        repo = RouteRepository(self.session)
        route = await repo.get(route_id)
        if route is None:
            raise ValueError("route not found")
        old = route.status
        route.status = RouteStatus.APPROVED
        await self._record(
            ctx, action="approve", entity_type="route", entity_id=route.id,
            old_values={"status": old.value},
            new_values={"status": route.status.value},
            event=RouteApproved(
                aggregate_id=route.id, site_id=ctx.site_id,
                product_id=route.product_id, version=route.version,
            ),
        )
        return route
