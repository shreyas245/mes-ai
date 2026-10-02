"""ISA-95 aligned SQLAlchemy base classes and mixins.

Pattern: **Template Method** via declarative mixins — every persistent entity
inherits common columns (surrogate id, timestamps, site scope, optimistic
version) without repeating them.

Design decision 2 in the architecture plan: every table maps to an ISA-95
object, so the base carries the vocabulary shared by all of them.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, server_default=func.now()
    )


class SiteScopedMixin:
    """Every record carries a ``site_id`` (plan decision 8: multi-site)."""

    site_id: Mapped[str] = mapped_column(String(64), index=True)


class VersionedMixin:
    """Optimistic concurrency version counter."""

    row_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Entity(Base, TimestampMixin, SiteScopedMixin, VersionedMixin):
    """Abstract root for every domain entity: UUID PK + common mixins."""

    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
