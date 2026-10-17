"""FastAPI application factory (Facade + Composition Root).

``create_app`` is the single place the modular monolith is assembled: it mounts
each module's router, installs the event subscribers (Observer wiring via the
module registry / Mediator) and, in dev, creates tables.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mes_core.config import get_settings
from mes_core.shared.base_models import Base
from mes_core.shared.db import get_engine
from mes_core.shared.registry import install_subscribers

logger = logging.getLogger(__name__)


def _import_models() -> None:
    """Import every module so SQLAlchemy sees all tables + events register."""
    import mes_core.compliance.models  # noqa: F401
    import mes_core.genealogy.models  # noqa: F401
    import mes_core.master_data.models  # noqa: F401
    import mes_core.performance.models  # noqa: F401
    import mes_core.plant_model.models  # noqa: F401
    import mes_core.production.models  # noqa: F401
    import mes_core.quality.models  # noqa: F401
    import mes_core.shared.audit  # noqa: F401
    import mes_core.shared.outbox  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _import_models()
    if get_settings().environment == "dev":
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    count = install_subscribers()
    logger.info("installed %d event subscribers", count)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="mes-core", version="0.1.0", lifespan=lifespan)

    # Import modules (registers routers + subscribers).
    from mes_core.compliance import router as compliance_router
    from mes_core.genealogy import router as genealogy_router
    from mes_core.master_data import router as master_data_router
    from mes_core.performance import router as performance_router
    from mes_core.plant_model import router as plant_model_router
    from mes_core.production import router as production_router
    from mes_core.quality import router as quality_router
    from mes_core.reporting import router as reporting_router

    for router in (
        plant_model_router,
        master_data_router,
        production_router,
        genealogy_router,
        performance_router,
        quality_router,
        compliance_router,
        reporting_router,
    ):
        app.include_router(router)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "env": settings.environment}

    return app


app = create_app()


def run() -> None:  # pragma: no cover - console entry point
    import uvicorn

    uvicorn.run("mes_core.main:app", host="0.0.0.0", port=8000, reload=True)
