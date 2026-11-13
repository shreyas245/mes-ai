"""Concrete report generators (each fills the Template Method steps)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mes_core.performance.models import OeeRollup
from mes_core.production.models import ProductionOrder
from mes_core.reporting.base import Renderer, ReportGenerator


class OrderSummaryReport(ReportGenerator):
    def __init__(self, session: AsyncSession, site_id: str, renderer: Renderer | None = None):
        super().__init__(renderer)
        self.session = session
        self.site_id = site_id

    def title(self) -> str:
        return f"Order Summary — {self.site_id}"

    def columns(self) -> list[str]:
        return ["order_no", "product_id", "state", "quantity"]

    async def collect_rows(self) -> list[dict[str, Any]]:
        stmt = select(ProductionOrder).where(ProductionOrder.site_id == self.site_id)
        orders = (await self.session.execute(stmt)).scalars().all()
        return [
            {
                "order_no": o.order_no, "product_id": o.product_id,
                "state": o.state.value, "quantity": o.quantity,
            }
            for o in orders
        ]


class OeeReport(ReportGenerator):
    def __init__(self, session: AsyncSession, site_id: str, renderer: Renderer | None = None):
        super().__init__(renderer)
        self.session = session
        self.site_id = site_id

    def title(self) -> str:
        return f"OEE Report — {self.site_id}"

    def columns(self) -> list[str]:
        return ["equipment_id", "availability", "performance", "quality", "oee"]

    async def collect_rows(self) -> list[dict[str, Any]]:
        stmt = select(OeeRollup).where(OeeRollup.site_id == self.site_id)
        rollups = (await self.session.execute(stmt)).scalars().all()
        return [
            {
                "equipment_id": r.equipment_id,
                "availability": round(r.availability, 3),
                "performance": round(r.performance, 3),
                "quality": round(r.quality, 3),
                "oee": round(r.oee, 3),
            }
            for r in rollups
        ]

    def summarize(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows:
            return {"row_count": 0}
        avg = sum(r["oee"] for r in rows) / len(rows)
        return {"row_count": len(rows), "avg_oee": round(avg, 3)}
