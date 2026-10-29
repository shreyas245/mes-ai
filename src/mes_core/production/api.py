"""Production REST API. Operator actions run through the CommandInvoker."""

from __future__ import annotations

from fastapi import APIRouter

from mes_core.production.commands import CompleteOperation, ConsumeLot, StartOperation
from mes_core.production.schemas import (
    CompletePayload,
    ConsumePayload,
    OperationOut,
    OrderCreate,
    OrderOut,
)
from mes_core.production.service import ProductionService
from mes_core.shared.commands import CommandInvoker
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/production", tags=["production"])
_invoker = CommandInvoker()


@router.post("/orders", response_model=OrderOut, status_code=201)
async def create_order(body: OrderCreate, ctx: ContextDep, session: SessionDep):
    return await ProductionService(session).create_order(ctx, **body.model_dump())


@router.post("/orders/{order_id}/release", response_model=OrderOut)
async def release_order(order_id: str, ctx: ContextDep, session: SessionDep):
    return await ProductionService(session).release_order(ctx, order_id)


@router.post("/operations/{operation_id}/start", response_model=OperationOut)
async def start_operation(operation_id: str, ctx: ContextDep, session: SessionDep):
    service = ProductionService(session)
    return await _invoker.run(StartOperation(service, ctx, operation_id), ctx)


@router.post("/operations/{operation_id}/complete", response_model=OperationOut)
async def complete_operation(
    operation_id: str, body: CompletePayload, ctx: ContextDep, session: SessionDep
):
    service = ProductionService(session)
    cmd = CompleteOperation(
        service, ctx, operation_id, body.good_count, body.scrap_count
    )
    return await _invoker.run(cmd, ctx)


@router.post("/operations/{operation_id}/consume", status_code=201)
async def consume(
    operation_id: str, body: ConsumePayload, ctx: ContextDep, session: SessionDep
):
    service = ProductionService(session)
    cmd = ConsumeLot(service, ctx, operation_id, body.lot_id, body.quantity)
    cons = await _invoker.run(cmd, ctx)
    return {"id": cons.id}
