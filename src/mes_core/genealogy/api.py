"""Genealogy REST API."""

from __future__ import annotations

from fastapi import APIRouter

from mes_core.genealogy.schemas import LotCreate, LotOut, TraceRow
from mes_core.genealogy.service import GenealogyService
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/genealogy", tags=["genealogy"])


@router.post("/lots", response_model=LotOut, status_code=201)
async def create_lot(body: LotCreate, ctx: ContextDep, session: SessionDep):
    return await GenealogyService(session).create_lot(ctx, **body.model_dump())


@router.get("/trace/forward/{lot_code}", response_model=list[TraceRow])
async def trace_forward(lot_code: str, session: SessionDep, ctx: ContextDep):
    rows = await GenealogyService(session).trace_forward(lot_code)
    return [TraceRow(depth=d, lot_code=c) for d, c in rows]


@router.get("/trace/backward/{lot_code}", response_model=list[TraceRow])
async def trace_backward(lot_code: str, session: SessionDep, ctx: ContextDep):
    rows = await GenealogyService(session).trace_backward(lot_code)
    return [TraceRow(depth=d, lot_code=c) for d, c in rows]
