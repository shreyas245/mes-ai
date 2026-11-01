"""Genealogy repositories, incl. recursive trace queries."""

from __future__ import annotations

from sqlalchemy import select

from mes_core.genealogy.models import GenealogyLink, MaterialLot
from mes_core.shared.repository import SqlAlchemyRepository


class MaterialLotRepository(SqlAlchemyRepository[MaterialLot]):
    model = MaterialLot

    async def by_code(self, lot_code: str) -> MaterialLot | None:
        stmt = select(MaterialLot).where(MaterialLot.lot_code == lot_code)
        return (await self.session.execute(stmt)).scalars().first()


class GenealogyLinkRepository(SqlAlchemyRepository[GenealogyLink]):
    model = GenealogyLink

    async def children_of(self, lot_id: str) -> list[GenealogyLink]:
        stmt = select(GenealogyLink).where(GenealogyLink.parent_lot_id == lot_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def parents_of(self, lot_id: str) -> list[GenealogyLink]:
        stmt = select(GenealogyLink).where(GenealogyLink.child_lot_id == lot_id)
        return list((await self.session.execute(stmt)).scalars().all())
