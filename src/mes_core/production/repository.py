"""Production repositories."""

from __future__ import annotations

from sqlalchemy import select

from mes_core.production.models import (
    OrderOperation,
    ProductionOrder,
)
from mes_core.shared.repository import SqlAlchemyRepository


class ProductionOrderRepository(SqlAlchemyRepository[ProductionOrder]):
    model = ProductionOrder


class OrderOperationRepository(SqlAlchemyRepository[OrderOperation]):
    model = OrderOperation

    async def for_order(self, order_id: str) -> list[OrderOperation]:
        stmt = (
            select(OrderOperation)
            .where(OrderOperation.order_id == order_id)
            .order_by(OrderOperation.sequence)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def dispatch_list(self, work_center_id: str) -> list[OrderOperation]:
        stmt = select(OrderOperation).where(
            OrderOperation.work_center_id == work_center_id
        )
        return list((await self.session.execute(stmt)).scalars().all())
