"""Transactional outbox (plan decision 4).

Domain events are written to ``outbox_event`` in the *same* DB transaction as the
state change, then a relay publishes them to the bus and marks them sent. This
guarantees no lost and no double-applied events.

Patterns:
- **Outbox** (messaging) with an at-least-once **relay**.
- **Factory Method** — ``build_event`` reconstructs typed events on relay.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.shared.base_models import Base
from mes_core.shared.event_bus import EventBus, get_event_bus
from mes_core.shared.events import DomainEvent, build_event

logger = logging.getLogger(__name__)


class OutboxEvent(Base):
    __tablename__ = "outbox_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    aggregate_id: Mapped[str] = mapped_column(String(36), index=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


def enqueue(session: AsyncSession, event: DomainEvent) -> None:
    """Add an event to the outbox within the caller's transaction.

    No commit here — the service commits atomically with its state change.
    """
    session.add(
        OutboxEvent(
            event_id=event.event_id,
            name=event.name,
            aggregate_id=event.aggregate_id,
            site_id=event.site_id,
            payload_json=json.dumps(event.payload()),
        )
    )


class OutboxRelay:
    """Polls unsent outbox rows and publishes them to the bus."""

    def __init__(self, bus: EventBus | None = None, batch_size: int = 100) -> None:
        self._bus = bus or get_event_bus()
        self._batch_size = batch_size

    async def relay_once(self, session: AsyncSession) -> int:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.sent_at.is_(None))
            .order_by(OutboxEvent.id)
            .limit(self._batch_size)
        )
        rows = (await session.execute(stmt)).scalars().all()
        for row in rows:
            event = build_event(row.name, json.loads(row.payload_json))
            await self._bus.publish(event)
            row.sent_at = datetime.now(timezone.utc)
        if rows:
            await session.commit()
        return len(rows)
