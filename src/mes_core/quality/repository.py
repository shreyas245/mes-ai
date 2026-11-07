"""Quality repositories."""

from __future__ import annotations

from mes_core.quality.models import (
    Characteristic,
    InspectionPlan,
    InspectionResult,
    Nonconformance,
)
from mes_core.shared.repository import SqlAlchemyRepository


class InspectionPlanRepository(SqlAlchemyRepository[InspectionPlan]):
    model = InspectionPlan


class CharacteristicRepository(SqlAlchemyRepository[Characteristic]):
    model = Characteristic


class InspectionResultRepository(SqlAlchemyRepository[InspectionResult]):
    model = InspectionResult


class NonconformanceRepository(SqlAlchemyRepository[Nonconformance]):
    model = Nonconformance
