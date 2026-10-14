"""Service base classes.

Patterns:
- **Facade** — each module exposes one service as its only public surface; other
  modules call the service, never the tables (plan decision 1).
- **Template Method** — :class:`DomainService` centralizes the transactional +
  audit + outbox ritual so concrete services only write domain logic.
- **Decorator** — :class:`AuditedService` can wrap any service to add auditing
  transparently (shown here for completeness; most services use the mixin).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from mes_core.shared.audit import AuditTrail
from mes_core.shared.context import OperationContext
from mes_core.shared.events import DomainEvent
from mes_core.shared.outbox import enqueue


class DomainService:
    """Base for module services.

    Holds the session + audit trail and provides the shared helper every service
    uses to record a change: audit entry + outbox event in one transaction.
    """

    def __init__(self, session: AsyncSession, audit: AuditTrail | None = None) -> None:
        self.session = session
        self.audit = audit or AuditTrail()

    async def _record(
        self,
        ctx: OperationContext,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        event: DomainEvent | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> None:
        """Template step: write audit + (optionally) an outbox event.

        The caller's ``session_scope`` commits both atomically with the change.
        """
        await self.audit.record(
            self.session,
            actor=ctx.actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
            site_id=ctx.site_id,
        )
        if event is not None:
            enqueue(self.session, event)
