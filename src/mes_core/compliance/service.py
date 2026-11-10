"""Compliance service (Facade over the shared audit trail + e-signatures).

Exposes a clean API for the audit viewer and for capturing electronic
signatures. Signing requires re-authentication in production (Keycloak); here it
records the signer + meaning and relies on RBAC for identity.
"""

from __future__ import annotations

from datetime import datetime, timezone

from mes_core.compliance.models import ElectronicSignature
from mes_core.shared.audit import AuditLog, AuditTrail
from mes_core.shared.context import OperationContext
from mes_core.shared.service import DomainService
from sqlalchemy import select


class ComplianceService(DomainService):
    async def verify_audit_chain(self) -> bool:
        """Re-walk the hash chain; False means tampering was detected."""
        return await AuditTrail().verify_chain(self.session)

    async def audit_entries(self, *, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def sign(
        self, ctx: OperationContext, *, entity_type: str, entity_id: str, meaning: str
    ) -> ElectronicSignature:
        sig = ElectronicSignature(
            site_id=ctx.site_id, entity_type=entity_type, entity_id=entity_id,
            signer=ctx.actor, meaning=meaning,
            signed_at=datetime.now(timezone.utc),
        )
        self.session.add(sig)
        await self.session.flush()
        await self._record(
            ctx, action="sign", entity_type="electronic_signature",
            entity_id=sig.id, new_values={"meaning": meaning, "target": entity_id},
        )
        return sig
