"""Performance service (module Facade): downtime, reason codes, OEE rollups."""

from __future__ import annotations

from datetime import datetime, timezone

from mes_core.performance.events import DowntimeReasonAssigned, MachineStateChanged
from mes_core.performance.models import (
    DowntimeEvent,
    MachineStateEvent,
    OeeRollup,
    ReasonCode,
)
from mes_core.performance.oee import OeeCalculator, OeeInputs
from mes_core.performance.repository import (
    DowntimeRepository,
    OeeRollupRepository,
    ReasonCodeRepository,
)
from mes_core.shared.context import OperationContext
from mes_core.shared.rbac import authorize
from mes_core.shared.service import DomainService


class PerformanceService(DomainService):
    def __init__(self, session, audit=None, calculator: OeeCalculator | None = None):
        super().__init__(session, audit)
        self.calculator = calculator or OeeCalculator()

    async def add_reason_code(
        self, ctx: OperationContext, *, code: str, label: str,
        parent_id: str | None = None,
    ) -> ReasonCode:
        authorize(ctx, ctx.site_id, required_role="engineer")
        rc = ReasonCode(site_id=ctx.site_id, code=code, label=label, parent_id=parent_id)
        ReasonCodeRepository(self.session).add(rc)
        await self.session.flush()
        return rc

    async def record_machine_state(
        self, ctx: OperationContext, *, equipment_id: str, state: str
    ) -> MachineStateEvent:
        ev = MachineStateEvent(
            site_id=ctx.site_id, equipment_id=equipment_id, state=state,
            at=datetime.now(timezone.utc),
        )
        self.session.add(ev)
        await self.session.flush()
        await self._record(
            ctx, action="machine_state", entity_type="machine_state_event",
            entity_id=ev.id, new_values={"state": state},
            event=MachineStateChanged(
                aggregate_id=equipment_id, site_id=ctx.site_id,
                equipment_id=equipment_id, state=state,
            ),
        )
        return ev

    async def assign_downtime_reason(
        self, ctx: OperationContext, downtime_id: str, reason_code_id: str
    ) -> DowntimeEvent:
        authorize(ctx, ctx.site_id, required_role="operator")
        repo = DowntimeRepository(self.session)
        dt = await repo.get(downtime_id)
        if dt is None:
            raise ValueError("downtime event not found")
        dt.reason_code_id = reason_code_id
        await self._record(
            ctx, action="assign_reason", entity_type="downtime_event",
            entity_id=dt.id, new_values={"reason_code_id": reason_code_id},
            event=DowntimeReasonAssigned(
                aggregate_id=dt.id, site_id=ctx.site_id,
                equipment_id=dt.equipment_id, reason_code_id=reason_code_id,
            ),
        )
        return dt

    async def compute_rollup(
        self, ctx: OperationContext, *, equipment_id: str, inputs: OeeInputs,
        window_start: datetime | None = None,
    ) -> OeeRollup:
        result = self.calculator.calculate(inputs)
        rollup = OeeRollup(
            site_id=ctx.site_id, equipment_id=equipment_id,
            window_start=window_start or datetime.now(timezone.utc),
            availability=result.availability, performance=result.performance,
            quality=result.quality, oee=result.oee,
        )
        OeeRollupRepository(self.session).add(rollup)
        await self.session.flush()
        return rollup
