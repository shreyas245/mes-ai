"""Generic async repository (Repository pattern + Template Method).

Each module defines table-specific repositories by subclassing
:class:`SqlAlchemyRepository` and setting ``model``. This keeps modules from
touching each other's tables (plan decision 1: strict module boundaries).
"""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mes_core.shared.base_models import Entity

T = TypeVar("T", bound=Entity)


class SqlAlchemyRepository(Generic[T]):
    """Common CRUD over a single aggregate, scoped by site."""

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: str) -> T | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, *, site_id: str | None = None, limit: int = 100) -> list[T]:
        stmt = select(self.model)
        if site_id is not None:
            stmt = stmt.where(self.model.site_id == site_id)
        stmt = stmt.limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    def add(self, entity: T) -> T:
        self.session.add(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
