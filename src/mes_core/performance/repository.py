"""Performance repositories."""

from __future__ import annotations

from mes_core.performance.models import (
    DowntimeEvent,
    MachineStateEvent,
    OeeRollup,
    ReasonCode,
)
from mes_core.shared.repository import SqlAlchemyRepository


class ReasonCodeRepository(SqlAlchemyRepository[ReasonCode]):
    model = ReasonCode


class MachineStateRepository(SqlAlchemyRepository[MachineStateEvent]):
    model = MachineStateEvent


class DowntimeRepository(SqlAlchemyRepository[DowntimeEvent]):
    model = DowntimeEvent


class OeeRollupRepository(SqlAlchemyRepository[OeeRollup]):
    model = OeeRollup
