"""Request/operation context — who is acting, and in which site scope.

A small immutable value object passed into services and commands so that audit,
RBAC and site-scoping all read the same authenticated identity.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class OperationContext:
    actor: str
    site_id: str
    roles: frozenset[str] = field(default_factory=frozenset)
    #: Client-generated id for idempotent retries (NFR: no duplicated counts).
    request_id: str | None = None

    def has_role(self, role: str) -> bool:
        return role in self.roles
