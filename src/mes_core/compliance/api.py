"""Compliance REST API: audit viewer + e-signatures."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from mes_core.compliance.service import ComplianceService
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/compliance", tags=["compliance"])


class SignRequest(BaseModel):
    entity_type: str
    entity_id: str
    meaning: str


@router.get("/audit")
async def list_audit(session: SessionDep, ctx: ContextDep, limit: int = 100):
    rows = await ComplianceService(session).audit_entries(limit=limit)
    return [
        {
            "id": r.id, "actor": r.actor, "action": r.action,
            "entity_type": r.entity_type, "entity_id": r.entity_id,
            "occurred_at": r.occurred_at, "entry_hash": r.entry_hash,
        }
        for r in rows
    ]


@router.get("/audit/verify")
async def verify_audit(session: SessionDep, ctx: ContextDep):
    return {"intact": await ComplianceService(session).verify_audit_chain()}


@router.post("/signatures", status_code=201)
async def sign(body: SignRequest, ctx: ContextDep, session: SessionDep):
    sig = await ComplianceService(session).sign(ctx, **body.model_dump())
    return {"id": sig.id, "signer": sig.signer, "meaning": sig.meaning}
