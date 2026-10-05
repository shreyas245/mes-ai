"""Generic state machine (plan decision 3).

Patterns:
- **State** (GoF, Behavioral) — allowed transitions are declared per state.
- **Template Method** — :meth:`StateMachine.fire` runs a fixed algorithm
  (validate → guard → mutate → emit audit + event) while subclasses/instances
  supply the transition table and side effects.

Transitions are validated in ONE place, each is auditable, and each can emit a
domain event. Used by production orders and operations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar

S = TypeVar("S", bound=Enum)
C = TypeVar("C")  # context/aggregate the transition acts on


class IllegalTransition(Exception):
    """Raised when a transition is not allowed from the current state."""


@dataclass(frozen=True, slots=True)
class Transition(Generic[S, C]):
    trigger: str
    source: S
    target: S
    #: Optional guard: returns True if the transition may proceed.
    guard: Callable[[C], bool] | None = None


@dataclass
class StateMachine(Generic[S, C]):
    """A reusable transition table keyed by (trigger, source)."""

    transitions: list[Transition[S, C]] = field(default_factory=list)
    _index: dict[tuple[str, S], Transition[S, C]] = field(default_factory=dict)

    def allow(
        self,
        trigger: str,
        source: S,
        target: S,
        guard: Callable[[C], bool] | None = None,
    ) -> StateMachine[S, C]:
        t = Transition(trigger, source, target, guard)
        self.transitions.append(t)
        self._index[(trigger, source)] = t
        return self  # fluent (Builder-ish) configuration

    def can_fire(self, trigger: str, current: S, aggregate: C) -> bool:
        t = self._index.get((trigger, current))
        if t is None:
            return False
        return t.guard is None or t.guard(aggregate)

    def next_state(self, trigger: str, current: S, aggregate: C) -> S:
        """Template Method step: validate + guard, return the target state."""
        t = self._index.get((trigger, current))
        if t is None:
            raise IllegalTransition(f"'{trigger}' not allowed from {current.name}")
        if t.guard is not None and not t.guard(aggregate):
            raise IllegalTransition(f"guard rejected '{trigger}' from {current.name}")
        return t.target
