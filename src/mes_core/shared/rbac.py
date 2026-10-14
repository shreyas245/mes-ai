"""Role/site-scoped access control (plan: RBAC by role + site/area scope).

Built as a **Chain of Responsibility**: an authenticated request passes through
an authentication check, then a site-scope check, then a role check.
"""

from __future__ import annotations

from dataclasses import dataclass

from mes_core.shared.chain import CheckResult, Handler, build_chain
from mes_core.shared.context import OperationContext


class AccessDenied(Exception):
    pass


@dataclass(slots=True)
class AccessRequest:
    ctx: OperationContext
    target_site_id: str
    required_role: str


class _Authenticated(Handler[AccessRequest]):
    def check(self, request: AccessRequest) -> CheckResult:
        if not request.ctx.actor:
            return CheckResult.failed("not authenticated")
        return CheckResult.passed()


class _SiteScope(Handler[AccessRequest]):
    def check(self, request: AccessRequest) -> CheckResult:
        if request.ctx.site_id != request.target_site_id:
            return CheckResult.failed(
                f"actor scoped to {request.ctx.site_id}, not {request.target_site_id}"
            )
        return CheckResult.passed()


class _RequiredRole(Handler[AccessRequest]):
    def check(self, request: AccessRequest) -> CheckResult:
        if not request.ctx.has_role(request.required_role):
            return CheckResult.failed(f"missing role '{request.required_role}'")
        return CheckResult.passed()


_CHAIN = build_chain(_Authenticated(), _SiteScope(), _RequiredRole())


def authorize(ctx: OperationContext, target_site_id: str, required_role: str) -> None:
    """Raise :class:`AccessDenied` unless the full chain passes."""
    result = _CHAIN.handle(AccessRequest(ctx, target_site_id, required_role))
    if not result.ok:
        raise AccessDenied(result.message)
