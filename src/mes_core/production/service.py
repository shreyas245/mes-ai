"""Production service (module Facade).

Owns orders, operations, executions, consumption, output and data collection.
Every state change goes through the shared state machines so transitions are
validated in one place and produce an audit entry + outbox event.
"""

from __future__ import annotations

from datetime import datetime, timezone

from mes_core.production.events import (
    MaterialConsumed,
    OperationCompleted,
    OperationStarted,
    OrderReleased,
)
from mes_core.production.models import (
    MaterialConsumption,
    OperationExecution,
    OrderOperation,
    ProductionOrder,
    ProductionOutput,
)
from mes_core.production.repository import (
    OrderOperationRepository,
    ProductionOrderRepository,
)
from mes_core.production.states import (
    OPERATION_MACHINE,
    ORDER_MACHINE,
    OperationState,
    OrderState,
)
from mes_core.shared.context import OperationContext
from mes_core.shared.rbac import authorize
from mes_core.shared.service import DomainService


class ProductionService(DomainService):
    @property
    def orders(self) -> ProductionOrderRepository:
        return ProductionOrderRepository(self.session)

    @property
    def operations(self) -> OrderOperationRepository:
        return OrderOperationRepository(self.session)

    # --- orders ---------------------------------------------------------------

    async def create_order(
        self, ctx: OperationContext, *, order_no: str, product_id: str,
        route_id: str, quantity: float, line_id: str | None = None,
    ) -> ProductionOrder:
        authorize(ctx, ctx.site_id, required_role="supervisor")
        order = ProductionOrder(
            site_id=ctx.site_id, order_no=order_no, product_id=product_id,
            route_id=route_id, quantity=quantity, line_id=line_id,
        )
        self.orders.add(order)
        await self.session.flush()
        await self._record(
            ctx, action="create", entity_type="production_order",
            entity_id=order.id, new_values={"order_no": order_no},
        )
        return order

    async def _transition_order(
        self, ctx: OperationContext, order: ProductionOrder, trigger: str
    ) -> OrderState:
        old = order.state
        target = ORDER_MACHINE.next_state(trigger, old, order)
        order.state = target
        return old

    async def release_order(
        self, ctx: OperationContext, order_id: str
    ) -> ProductionOrder:
        authorize(ctx, ctx.site_id, required_role="supervisor")
        order = await self._require_order(order_id)
        old = await self._transition_order(ctx, order, "release")
        await self._record(
            ctx, action="release", entity_type="production_order",
            entity_id=order.id, old_values={"state": old.value},
            new_values={"state": order.state.value},
            event=OrderReleased(
                aggregate_id=order.id, site_id=ctx.site_id,
                order_no=order.order_no, line_id=order.line_id or "",
            ),
        )
        return order

    # --- operations -----------------------------------------------------------

    async def add_operation(
        self, ctx: OperationContext, *, order_id: str, route_step_id: str,
        sequence: int, work_center_id: str | None = None,
    ) -> OrderOperation:
        op = OrderOperation(
            site_id=ctx.site_id, order_id=order_id, route_step_id=route_step_id,
            sequence=sequence, work_center_id=work_center_id,
            state=OperationState.READY,
        )
        self.operations.add(op)
        await self.session.flush()
        return op

    async def start_operation(
        self, ctx: OperationContext, operation_id: str
    ) -> OrderOperation:
        authorize(ctx, ctx.site_id, required_role="operator")
        op = await self._require_operation(operation_id)
        old = op.state
        op.state = OPERATION_MACHINE.next_state("start", old, op)
        self.session.add(
            OperationExecution(
                site_id=ctx.site_id, operation_id=op.id, operator=ctx.actor,
                started_at=datetime.now(timezone.utc),
            )
        )
        await self._record(
            ctx, action="start", entity_type="order_operation", entity_id=op.id,
            old_values={"state": old.value}, new_values={"state": op.state.value},
            event=OperationStarted(
                aggregate_id=op.id, site_id=ctx.site_id,
                order_id=op.order_id, work_center_id=op.work_center_id or "",
            ),
        )
        return op

    async def complete_operation(
        self, ctx: OperationContext, operation_id: str,
        *, good_count: float, scrap_count: float = 0.0,
    ) -> OrderOperation:
        authorize(ctx, ctx.site_id, required_role="operator")
        op = await self._require_operation(operation_id)
        old = op.state
        op.state = OPERATION_MACHINE.next_state("complete", old, op)
        op.good_count += good_count
        op.scrap_count += scrap_count
        await self._record(
            ctx, action="complete", entity_type="order_operation", entity_id=op.id,
            old_values={"state": old.value},
            new_values={"state": op.state.value, "good": op.good_count},
            event=OperationCompleted(
                aggregate_id=op.id, site_id=ctx.site_id, order_id=op.order_id,
                good_count=good_count, scrap_count=scrap_count,
            ),
        )
        return op

    async def consume(
        self, ctx: OperationContext, operation_id: str,
        *, lot_id: str, quantity: float,
    ) -> MaterialConsumption:
        authorize(ctx, ctx.site_id, required_role="operator")
        cons = MaterialConsumption(
            site_id=ctx.site_id, operation_id=operation_id,
            lot_id=lot_id, quantity=quantity,
        )
        self.session.add(cons)
        await self.session.flush()
        await self._record(
            ctx, action="consume", entity_type="material_consumption",
            entity_id=cons.id, new_values={"lot_id": lot_id, "quantity": quantity},
            event=MaterialConsumed(
                aggregate_id=cons.id, site_id=ctx.site_id,
                operation_id=operation_id, lot_id=lot_id, quantity=quantity,
            ),
        )
        return cons

    async def record_output(
        self, ctx: OperationContext, operation_id: str,
        *, lot_id: str, quantity: float,
    ) -> ProductionOutput:
        out = ProductionOutput(
            site_id=ctx.site_id, operation_id=operation_id,
            lot_id=lot_id, quantity=quantity,
        )
        self.session.add(out)
        await self.session.flush()
        return out

    # --- helpers --------------------------------------------------------------

    async def _require_order(self, order_id: str) -> ProductionOrder:
        order = await self.orders.get(order_id)
        if order is None:
            raise ValueError("order not found")
        return order

    async def _require_operation(self, operation_id: str) -> OrderOperation:
        op = await self.operations.get(operation_id)
        if op is None:
            raise ValueError("operation not found")
        return op
