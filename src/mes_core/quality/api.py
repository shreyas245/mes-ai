"""Quality REST API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from mes_core.quality.checks import Measurement as CheckInput
from mes_core.quality.repository import InspectionPlanRepository
from mes_core.quality.schemas import CharacteristicCreate, InProcessCheck, PlanCreate
from mes_core.quality.service import OperationBlocked, QualityService
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/quality", tags=["quality"])


@router.post("/plans", status_code=201)
async def create_plan(body: PlanCreate, ctx: ContextDep, session: SessionDep):
    plan = await QualityService(session).create_plan(ctx, **body.model_dump())
    return {"id": plan.id, "code": plan.code}


@router.post("/characteristics", status_code=201)
async def add_characteristic(
    body: CharacteristicCreate, ctx: ContextDep, session: SessionDep
):
    ch = await QualityService(session).add_characteristic(ctx, **body.model_dump())
    return {"id": ch.id}


@router.post("/in-process-check")
async def in_process_check(body: InProcessCheck, ctx: ContextDep, session: SessionDep):
    service = QualityService(session)
    plan = await InspectionPlanRepository(session).get(body.plan_id)
    if plan is None:
        raise HTTPException(404, "plan not found")
    measurements = [
        CheckInput(m.characteristic, m.value, m.lower, m.upper)
        for m in body.measurements
    ]
    try:
        result = await service.run_in_process_check(
            ctx, plan=plan, operation_id=body.operation_id,
            lot_id=body.lot_id, measurements=measurements,
        )
    except OperationBlocked as exc:
        # Operation blocked by a failed blocking inspection.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": result.id, "passed": result.passed}
