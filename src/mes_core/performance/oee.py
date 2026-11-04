"""OEE computation (plan Phase 3 / FactoryTalk Metrics).

Pattern: **Strategy** (GoF, Behavioral). OEE = Availability × Performance ×
Quality, but plants compute each factor differently (time models, ideal cycle
time, scrap handling). Each factor is a pluggable strategy; ``OeeCalculator``
composes them so the policy can vary per site without touching the engine.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OeeInputs:
    planned_time_s: float
    run_time_s: float
    ideal_cycle_time_s: float
    total_count: float
    good_count: float


class AvailabilityStrategy(abc.ABC):
    @abc.abstractmethod
    def compute(self, i: OeeInputs) -> float: ...


class PerformanceStrategy(abc.ABC):
    @abc.abstractmethod
    def compute(self, i: OeeInputs) -> float: ...


class QualityStrategy(abc.ABC):
    @abc.abstractmethod
    def compute(self, i: OeeInputs) -> float: ...


class StandardAvailability(AvailabilityStrategy):
    def compute(self, i: OeeInputs) -> float:
        return _ratio(i.run_time_s, i.planned_time_s)


class StandardPerformance(PerformanceStrategy):
    def compute(self, i: OeeInputs) -> float:
        if i.run_time_s <= 0:
            return 0.0
        return _clamp((i.ideal_cycle_time_s * i.total_count) / i.run_time_s)


class StandardQuality(QualityStrategy):
    def compute(self, i: OeeInputs) -> float:
        return _ratio(i.good_count, i.total_count)


@dataclass(frozen=True, slots=True)
class OeeResult:
    availability: float
    performance: float
    quality: float

    @property
    def oee(self) -> float:
        return self.availability * self.performance * self.quality


class OeeCalculator:
    """Composes the three strategies into an OEE result."""

    def __init__(
        self,
        availability: AvailabilityStrategy | None = None,
        performance: PerformanceStrategy | None = None,
        quality: QualityStrategy | None = None,
    ) -> None:
        self._a = availability or StandardAvailability()
        self._p = performance or StandardPerformance()
        self._q = quality or StandardQuality()

    def calculate(self, i: OeeInputs) -> OeeResult:
        return OeeResult(self._a.compute(i), self._p.compute(i), self._q.compute(i))


def _ratio(num: float, den: float) -> float:
    return _clamp(num / den) if den > 0 else 0.0


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))
