"""SPC rule evaluation (Strategy).

Western Electric rules are each a strategy over a window of samples. Callers run
whichever set the characteristic requires. Only a couple are implemented here;
more plug in by adding strategies to the list.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ControlLimits:
    mean: float
    sigma: float


class SpcRule(abc.ABC):
    code: str

    @abc.abstractmethod
    def violated(self, samples: list[float], limits: ControlLimits) -> bool: ...


class Rule1_BeyondThreeSigma(SpcRule):
    code = "WE-1"

    def violated(self, samples: list[float], limits: ControlLimits) -> bool:
        if not samples:
            return False
        last = samples[-1]
        return abs(last - limits.mean) > 3 * limits.sigma


class Rule2_NinePointsOneSide(SpcRule):
    code = "WE-2"

    def violated(self, samples: list[float], limits: ControlLimits) -> bool:
        if len(samples) < 9:
            return False
        window = samples[-9:]
        return all(s > limits.mean for s in window) or all(
            s < limits.mean for s in window
        )


DEFAULT_RULES: list[SpcRule] = [Rule1_BeyondThreeSigma(), Rule2_NinePointsOneSide()]


def evaluate(
    samples: list[float], limits: ControlLimits, rules: list[SpcRule] | None = None
) -> list[str]:
    """Return codes of violated rules."""
    return [r.code for r in (rules or DEFAULT_RULES) if r.violated(samples, limits)]
