"""Derive machine state from tag readings (Strategy, GoF Behavioral).

A machine's state (Running / Idle / Down / Blocked / Starved) is derived from raw
tags by configurable rules. Each rule is a strategy; the first matching rule
wins. Plants tune rules without changing the gateway.
"""

from __future__ import annotations

import abc
import enum
from dataclasses import dataclass


class MachineState(str, enum.Enum):
    RUNNING = "running"
    IDLE = "idle"
    DOWN = "down"
    BLOCKED = "blocked"
    STARVED = "starved"
    UNKNOWN = "unknown"


class StateRule(abc.ABC):
    @abc.abstractmethod
    def evaluate(self, tags: dict[str, float | bool | str]) -> MachineState | None: ...


@dataclass(frozen=True, slots=True)
class FaultRule(StateRule):
    fault_tag: str

    def evaluate(self, tags):
        return MachineState.DOWN if tags.get(self.fault_tag) else None


@dataclass(frozen=True, slots=True)
class SpeedRule(StateRule):
    speed_tag: str
    running_threshold: float = 0.1

    def evaluate(self, tags):
        speed = tags.get(self.speed_tag)
        if speed is None:
            return None
        return MachineState.RUNNING if float(speed) > self.running_threshold else MachineState.IDLE


@dataclass(frozen=True, slots=True)
class StarvedBlockedRule(StateRule):
    infeed_tag: str
    outfeed_tag: str

    def evaluate(self, tags):
        if tags.get(self.infeed_tag) is False:
            return MachineState.STARVED
        if tags.get(self.outfeed_tag) is False:
            return MachineState.BLOCKED
        return None


class StateDeriver:
    """Runs ordered rules; first non-None result wins."""

    def __init__(self, rules: list[StateRule]) -> None:
        self._rules = rules

    def derive(self, tags: dict[str, float | bool | str]) -> MachineState:
        for rule in self._rules:
            state = rule.evaluate(tags)
            if state is not None:
                return state
        return MachineState.UNKNOWN
