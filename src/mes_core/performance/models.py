"""Performance ORM: machine states, downtime, reason codes, OEE rollups, shifts.

``machine_state_event``, ``tag_value`` and ``oee_rollup`` are TimescaleDB
hypertables in production; here they are ordinary tables so the stack runs on
plain Postgres/SQLite for dev.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from mes_core.shared.base_models import Entity


class ReasonCode(Entity):
    """Downtime reason, arranged as a tree (Composite): category → reason."""

    __tablename__ = "reason_code"

    code: Mapped[str] = mapped_column(String(64), index=True)
    label: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("reason_code.id"), default=None, index=True
    )


class MachineStateEvent(Entity):
    __tablename__ = "machine_state_event"

    equipment_id: Mapped[str] = mapped_column(String(36), index=True)
    state: Mapped[str] = mapped_column(String(32), index=True)  # running/idle/down/...
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class DowntimeEvent(Entity):
    __tablename__ = "downtime_event"

    equipment_id: Mapped[str] = mapped_column(String(36), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    reason_code_id: Mapped[str | None] = mapped_column(
        ForeignKey("reason_code.id"), default=None
    )


class OeeRollup(Entity):
    __tablename__ = "oee_rollup"

    equipment_id: Mapped[str] = mapped_column(String(36), index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    availability: Mapped[float] = mapped_column(Float, default=0.0)
    performance: Mapped[float] = mapped_column(Float, default=0.0)
    quality: Mapped[float] = mapped_column(Float, default=0.0)
    oee: Mapped[float] = mapped_column(Float, default=0.0)


class Shift(Entity):
    __tablename__ = "shift"

    name: Mapped[str] = mapped_column(String(64))
    start_minute: Mapped[int] = mapped_column(Integer)  # minutes from midnight
    duration_minutes: Mapped[int] = mapped_column(Integer)
