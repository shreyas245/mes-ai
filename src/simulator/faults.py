"""Fault injection (Strategy + Decorator).

Each fault is a strategy that perturbs a station's tick (a jam stops output, a
micro-stop pauses briefly, a speed loss reduces rate). Faults are composed as
decorators around a station's normal behavior.
"""

from __future__ import annotations

import abc
import random
from dataclasses import dataclass


@dataclass
class StationTick:
    running: bool
    speed: float  # units/min
    produced: int
    fault: str | None = None


class Fault(abc.ABC):
    @abc.abstractmethod
    def apply(self, tick: StationTick) -> StationTick: ...


@dataclass
class Jam(Fault):
    probability: float = 0.02

    def apply(self, tick: StationTick) -> StationTick:
        if random.random() < self.probability:
            return StationTick(running=False, speed=0.0, produced=0, fault="jam")
        return tick


@dataclass
class MicroStop(Fault):
    probability: float = 0.05

    def apply(self, tick: StationTick) -> StationTick:
        if random.random() < self.probability:
            return StationTick(running=False, speed=0.0, produced=0, fault="micro_stop")
        return tick


@dataclass
class SpeedLoss(Fault):
    factor: float = 0.7
    probability: float = 0.1

    def apply(self, tick: StationTick) -> StationTick:
        if random.random() < self.probability:
            return StationTick(
                running=tick.running,
                speed=tick.speed * self.factor,
                produced=int(tick.produced * self.factor),
                fault="speed_loss",
            )
        return tick
