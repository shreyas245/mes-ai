"""Visitor + recursive trace: L-100 → L-200 forward, and backward."""

from __future__ import annotations

from mes_core.genealogy.service import GenealogyService
from tests.conftest import make_ctx


async def test_forward_and_backward_trace(session):
    svc = GenealogyService(session)
    ctx = make_ctx()
    parent = await svc.create_lot(ctx, lot_code="L-100", material_id="M1", quantity=10)
    child = await svc.create_lot(ctx, lot_code="L-200", material_id="M2", quantity=5)
    await svc.link(ctx, parent_lot_id=parent.id, child_lot_id=child.id)
    await session.commit()

    forward = await svc.trace_forward("L-100")
    assert ("L-100", 0) == (forward[0][1], forward[0][0])
    assert any(code == "L-200" for _, code in forward)

    backward = await svc.trace_backward("L-200")
    assert any(code == "L-100" for _, code in backward)
