"""FastAPI dependencies shared across module routers.

In production the context comes from the Keycloak OIDC token (actor, site, roles).
For dev/demo we synthesize a context from headers with sensible defaults so the
API is usable without an identity provider running.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from mes_core.config import get_settings
from mes_core.shared.context import OperationContext
from mes_core.shared.db import get_session


async def current_context(
    x_actor: Annotated[str, Header()] = "dev-user",
    x_site_id: Annotated[str | None, Header()] = None,
    x_roles: Annotated[str, Header()] = "operator,engineer,supervisor,quality",
    x_request_id: Annotated[str | None, Header()] = None,
) -> OperationContext:
    site = x_site_id or get_settings().default_site_id
    roles = frozenset(r.strip() for r in x_roles.split(",") if r.strip())
    return OperationContext(
        actor=x_actor, site_id=site, roles=roles, request_id=x_request_id
    )


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ContextDep = Annotated[OperationContext, Depends(current_context)]
