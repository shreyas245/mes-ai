"""Quality service (module Facade): inspections, in-process checks, NCRs."""

from __future__ import annotations

from mes_core.quality.checks import Measurement as CheckInput
from mes_core.quality.checks import inspect
from mes_core.quality.events import InspectionFailed, LotPlacedOnHold
from mes_core.quality.models import (
    Characteristic,
    InspectionPlan,
    InspectionResult,
    Nonconformance,
)
from mes_core.quality.repository import (
    InspectionPlanRepository,
    NonconformanceRepository,
)
from mes_core.shared.context import OperationContext
from mes_core.shared.rbac import authorize
from mes_core.shared.service import DomainService


class OperationBlocked(Exception):
    """Raised when a blocking inspection fails an in-process check."""


class QualityService(DomainService):
    async def create_plan(
        self, ctx: OperationContext, *, code: str, name: str,
        route_step_id: str | None = None, blocking: bool = True,
    ) -> InspectionPlan:
        authorize(ctx, ctx.site_id, required_role="quality")
        plan = InspectionPlan(
            site_id=ctx.site_id, code=code, name=name,
            route_step_id=route_step_id, blocking=blocking,
        )
        InspectionPlanRepository(self.session).add(plan)
        await self.session.flush()
        return plan

    async def add_characteristic(
        self, ctx: OperationContext, *, plan_id: str, name: str,
        lower_limit: float | None = None, upper_limit: float | None = None,
        unit: str | None = None,
    ) -> Characteristic:
        authorize(ctx, ctx.site_id, required_role="quality")
        ch = Characteristic(
            site_id=ctx.site_id, plan_id=plan_id, name=name,
            lower_limit=lower_limit, upper_limit=upper_limit, unit=unit,
        )
        self.session.add(ch)
        await self.session.flush()
        return ch

    async def run_in_process_check(
        self, ctx: OperationContext, *, plan: InspectionPlan,
        operation_id: str, lot_id: str,
        measurements: list[CheckInput],
    ) -> InspectionResult:
        """Run the Chain-of-Responsibility checks; block operation if required."""
        authorize(ctx, ctx.site_id, required_role="operator")
        failures = [m for m in measurements if not inspect(m).ok]
        passed = not failures
        result = InspectionResult(
            site_id=ctx.site_id, plan_id=plan.id,
            operation_id=operation_id, lot_id=lot_id, passed=passed,
        )
        self.session.add(result)
        await self.session.flush()

        if not passed:
            await self._record(
                ctx, action="inspection_failed", entity_type="inspection_result",
                entity_id=result.id,
                new_values={"failures": [inspect(m).message for m in failures]},
                event=InspectionFailed(
                    aggregate_id=result.id, site_id=ctx.site_id,
                    plan_id=plan.id, operation_id=operation_id, lot_id=lot_id,
                ),
            )
            await self.place_lot_on_hold(
                ctx, lot_id=lot_id, reason="failed in-process inspection"
            )
            if plan.blocking:
                raise OperationBlocked(
                    "; ".join(inspect(m).message for m in failures)
                )
        return result

    async def place_lot_on_hold(
        self, ctx: OperationContext, *, lot_id: str, reason: str
    ) -> Nonconformance:
        ncr = Nonconformance(
            site_id=ctx.site_id, lot_id=lot_id, description=reason, status="hold",
        )
        NonconformanceRepository(self.session).add(ncr)
        await self.session.flush()
        await self._record(
            ctx, action="hold", entity_type="nonconformance", entity_id=ncr.id,
            new_values={"lot_id": lot_id, "reason": reason},
            event=LotPlacedOnHold(
                aggregate_id=lot_id, site_id=ctx.site_id, lot_id=lot_id, reason=reason
            ),
        )
        return ncr
