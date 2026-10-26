"""Operator actions as Command objects (GoF, Behavioral).

Each shop-floor action is a command executed via the shared ``CommandInvoker``,
which makes retries idempotent using the context ``request_id`` — satisfying the
NFR that queued operator-terminal actions never double-count after a network
blip. Commands are uniform and could equally be queued offline and replayed.
"""

from __future__ import annotations

from dataclasses import dataclass

from mes_core.production.models import OrderOperation
from mes_core.production.service import ProductionService
from mes_core.shared.commands import Command
from mes_core.shared.context import OperationContext


@dataclass
class StartOperation(Command[OrderOperation]):
    service: ProductionService
    ctx: OperationContext
    operation_id: str

    async def execute(self) -> OrderOperation:
        return await self.service.start_operation(self.ctx, self.operation_id)


@dataclass
class CompleteOperation(Command[OrderOperation]):
    service: ProductionService
    ctx: OperationContext
    operation_id: str
    good_count: float
    scrap_count: float = 0.0

    async def execute(self) -> OrderOperation:
        return await self.service.complete_operation(
            self.ctx, self.operation_id,
            good_count=self.good_count, scrap_count=self.scrap_count,
        )


@dataclass
class ConsumeLot(Command[object]):
    service: ProductionService
    ctx: OperationContext
    operation_id: str
    lot_id: str
    quantity: float

    async def execute(self) -> object:
        return await self.service.consume(
            self.ctx, self.operation_id, lot_id=self.lot_id, quantity=self.quantity
        )
