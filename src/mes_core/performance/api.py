"""Performance REST API (OEE, downtime, reason codes)."""

from __future__ import annotations

from fastapi import APIRouter

from mes_core.performance.oee import OeeInputs
from mes_core.performance.schemas import (
    MachineStateIn,
    OeeInputsIn,
    OeeRollupOut,
    ReasonCodeCreate,
)
from mes_core.performance.service import PerformanceService
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/performance", tags=["performance"])


@router.post("/reason-codes", status_code=201)
async def add_reason_code(body: ReasonCodeCreate, ctx: ContextDep, session: SessionDep):
    rc = await PerformanceService(session).add_reason_code(ctx, **body.model_dump())
    return {"id": rc.id, "code": rc.code}


@router.post("/machine-state", status_code=201)
async def machine_state(body: MachineStateIn, ctx: ContextDep, session: SessionDep):
    ev = await PerformanceService(session).record_machine_state(ctx, **body.model_dump())
    return {"id": ev.id}


@router.post("/oee", response_model=OeeRollupOut, status_code=201)
async def compute_oee(body: OeeInputsIn, ctx: ContextDep, session: SessionDep):
    inputs = OeeInputs(
        planned_time_s=body.planned_time_s,
        run_time_s=body.run_time_s,
        ideal_cycle_time_s=body.ideal_cycle_time_s,
        total_count=body.total_count,
        good_count=body.good_count,
    )
    return await PerformanceService(session).compute_rollup(
        ctx, equipment_id=body.equipment_id, inputs=inputs
    )
