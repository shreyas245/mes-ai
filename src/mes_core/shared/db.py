"""Database engine and session management.

Patterns:
- **Singleton** — one async engine / sessionmaker per process (cached).
- **Factory Method** — ``session_factory()`` manufactures configured sessions.

The async engine is created lazily so importing the package never touches a DB.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mes_core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Return the single async engine (Singleton)."""
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=settings.debug, future=True)


@lru_cache
def session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the cached session factory (Factory Method over the engine)."""
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Transactional scope: commit on success, roll back on error.

    This is the seam the Unit of Work builds upon.
    """
    session = session_factory()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped session."""
    async with session_scope() as session:
        yield session
