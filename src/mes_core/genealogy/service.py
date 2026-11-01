"""Genealogy service (module Facade): lots, links, forward/backward trace."""

from __future__ import annotations

from mes_core.genealogy.events import GenealogyLinked, LotProduced
from mes_core.genealogy.models import GenealogyLink, MaterialLot
from mes_core.genealogy.repository import (
    GenealogyLinkRepository,
    MaterialLotRepository,
)
from mes_core.genealogy.visitor import FlattenVisitor, LotNode
from mes_core.shared.context import OperationContext
from mes_core.shared.service import DomainService


class GenealogyService(DomainService):
    @property
    def lots(self) -> MaterialLotRepository:
        return MaterialLotRepository(self.session)

    @property
    def links(self) -> GenealogyLinkRepository:
        return GenealogyLinkRepository(self.session)

    async def create_lot(
        self, ctx: OperationContext, *, lot_code: str, material_id: str,
        quantity: float, uom: str = "EA", serial: str | None = None,
    ) -> MaterialLot:
        lot = MaterialLot(
            site_id=ctx.site_id, lot_code=lot_code, material_id=material_id,
            quantity=quantity, uom=uom, serial=serial,
        )
        self.lots.add(lot)
        await self.session.flush()
        await self._record(
            ctx, action="create", entity_type="material_lot", entity_id=lot.id,
            new_values={"lot_code": lot_code, "quantity": quantity},
            event=LotProduced(
                aggregate_id=lot.id, site_id=ctx.site_id,
                lot_code=lot_code, material_id=material_id,
            ),
        )
        return lot

    async def link(
        self, ctx: OperationContext, *, parent_lot_id: str, child_lot_id: str,
        order_id: str | None = None,
    ) -> GenealogyLink:
        link = GenealogyLink(
            site_id=ctx.site_id, parent_lot_id=parent_lot_id,
            child_lot_id=child_lot_id, order_id=order_id,
        )
        self.links.add(link)
        await self.session.flush()
        await self._record(
            ctx, action="link", entity_type="genealogy_link", entity_id=link.id,
            new_values={"parent": parent_lot_id, "child": child_lot_id},
            event=GenealogyLinked(
                aggregate_id=link.id, site_id=ctx.site_id,
                parent_lot_id=parent_lot_id, child_lot_id=child_lot_id,
            ),
        )
        return link

    async def _build_forward(self, lot: MaterialLot) -> LotNode:
        node = LotNode(lot.id, lot.lot_code)
        for link in await self.links.children_of(lot.id):
            child = await self.lots.get(link.child_lot_id)
            if child is not None:
                node.children.append(await self._build_forward(child))
        return node

    async def _build_backward(self, lot: MaterialLot) -> LotNode:
        node = LotNode(lot.id, lot.lot_code)
        for link in await self.links.parents_of(lot.id):
            parent = await self.lots.get(link.parent_lot_id)
            if parent is not None:
                node.children.append(await self._build_backward(parent))
        return node

    async def trace_forward(self, lot_code: str) -> list[tuple[int, str]]:
        lot = await self.lots.by_code(lot_code)
        if lot is None:
            return []
        root = await self._build_forward(lot)
        visitor = FlattenVisitor()
        root.accept(visitor)
        return visitor.rows

    async def trace_backward(self, lot_code: str) -> list[tuple[int, str]]:
        lot = await self.lots.by_code(lot_code)
        if lot is None:
            return []
        root = await self._build_backward(lot)
        visitor = FlattenVisitor()
        root.accept(visitor)
        return visitor.rows
