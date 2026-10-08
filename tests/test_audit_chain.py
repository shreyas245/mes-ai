"""Hash-chained audit log: tamper detection (Memento + integrity chain)."""

from __future__ import annotations

from sqlalchemy import select

from mes_core.shared.audit import AuditLog, AuditTrail
from tests.conftest import make_ctx


async def test_audit_chain_intact_then_tampered(session):
    trail = AuditTrail()
    ctx = make_ctx()
    for i in range(3):
        await trail.record(
            session, actor=ctx.actor, action="create", entity_type="thing",
            entity_id=f"T-{i}", new_values={"i": i}, site_id=ctx.site_id,
        )
    await session.commit()
    assert await trail.verify_chain(session) is True

    # Tamper with a stored row.
    row = (await session.execute(select(AuditLog).limit(1))).scalars().first()
    row.new_values = '{"i": 999}'
    await session.commit()
    assert await trail.verify_chain(session) is False
