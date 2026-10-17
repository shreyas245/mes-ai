"""Test fixtures: in-memory DB + schema, isolated event bus per test."""

from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from mes_core.main import _import_models
from mes_core.shared.base_models import Base
from mes_core.shared.context import OperationContext


@pytest_asyncio.fixture
async def session():
    _import_models()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


def make_ctx(**kw) -> OperationContext:
    defaults = dict(
        actor="tester",
        site_id="SITE-DEFAULT",
        roles=frozenset({"operator", "engineer", "supervisor", "quality"}),
    )
    defaults.update(kw)
    return OperationContext(**defaults)
