"""Append-only, hash-chained audit log (plan decision 7 / 21 CFR Part 11).

Patterns:
- **Memento** — each entry captures a before/after snapshot of the changed state.
- **Chain of integrity** — every row stores ``prev_hash`` and ``entry_hash``;
  ``entry_hash = sha256(prev_hash + canonical(entry))``. Any tampering breaks the
  chain and is detectable by :func:`verify_chain`.
- **Decorator** — :class:`AuditedService` wraps a service to record transitions
  without the service knowing about auditing (see ``shared/service.py``).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.config import get_settings
from mes_core.shared.base_models import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(128), index=True)
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str | None] = mapped_column(String(512), default=None)
    old_values: Mapped[str] = mapped_column(Text, default="{}")
    new_values: Mapped[str] = mapped_column(Text, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    prev_hash: Mapped[str] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), index=True)


def _canonical(entry: dict[str, Any]) -> str:
    return json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str)


def _hash(prev_hash: str, entry: dict[str, Any]) -> str:
    return hashlib.sha256((prev_hash + _canonical(entry)).encode()).hexdigest()


class AuditTrail:
    """Writes tamper-evident audit entries."""

    async def _last_hash(self, session: AsyncSession) -> str:
        stmt = select(AuditLog.entry_hash).order_by(AuditLog.id.desc()).limit(1)
        last = (await session.execute(stmt)).scalar_one_or_none()
        return last or get_settings().audit_genesis_hash

    async def record(
        self,
        session: AsyncSession,
        *,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        reason: str | None = None,
        site_id: str,
    ) -> AuditLog:
        prev = await self._last_hash(session)
        entry = {
            "site_id": site_id,
            "actor": actor,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "reason": reason,
            "old_values": old_values or {},
            "new_values": new_values or {},
        }
        row = AuditLog(
            site_id=site_id,
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
            old_values=json.dumps(old_values or {}, default=str),
            new_values=json.dumps(new_values or {}, default=str),
            prev_hash=prev,
            entry_hash=_hash(prev, entry),
        )
        session.add(row)
        return row

    async def verify_chain(self, session: AsyncSession) -> bool:
        """Re-walk the chain; return False if any link is broken (tampering)."""
        rows = (await session.execute(select(AuditLog).order_by(AuditLog.id))).scalars().all()
        prev = get_settings().audit_genesis_hash
        for row in rows:
            entry = {
                "site_id": row.site_id,
                "actor": row.actor,
                "action": row.action,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "reason": row.reason,
                "old_values": json.loads(row.old_values),
                "new_values": json.loads(row.new_values),
            }
            if row.prev_hash != prev or row.entry_hash != _hash(prev, entry):
                return False
            prev = row.entry_hash
        return True
