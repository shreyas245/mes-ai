"""Form validation rules DSL (Interpreter pattern, GoF Behavioral). Plan: Phase 2.

Engineers define checks like "weight within ±2 %" as JSON. Each rule node knows
how to ``interpret`` itself against a form's answers. New operators are new node
classes, so the grammar grows without touching the evaluator.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any


class Expression(abc.ABC):
    @abc.abstractmethod
    def interpret(self, context: dict[str, Any]) -> bool: ...


@dataclass(frozen=True, slots=True)
class Between(Expression):
    field: str
    low: float
    high: float

    def interpret(self, context: dict[str, Any]) -> bool:
        v = context.get(self.field)
        return v is not None and self.low <= float(v) <= self.high


@dataclass(frozen=True, slots=True)
class WithinPercent(Expression):
    field: str
    target: float
    percent: float

    def interpret(self, context: dict[str, Any]) -> bool:
        v = context.get(self.field)
        if v is None:
            return False
        tol = abs(self.target) * self.percent / 100.0
        return abs(float(v) - self.target) <= tol


@dataclass(frozen=True, slots=True)
class Required(Expression):
    field: str

    def interpret(self, context: dict[str, Any]) -> bool:
        return context.get(self.field) not in (None, "")


@dataclass(frozen=True, slots=True)
class And(Expression):
    parts: tuple[Expression, ...]

    def interpret(self, context: dict[str, Any]) -> bool:
        return all(p.interpret(context) for p in self.parts)


_OPS = {"between": Between, "within_percent": WithinPercent, "required": Required}


def parse(rule: dict[str, Any]) -> Expression:
    """Build an Expression tree from a JSON rule definition."""
    op = rule["op"]
    if op == "and":
        return And(tuple(parse(r) for r in rule["rules"]))
    cls = _OPS[op]
    return cls(**{k: v for k, v in rule.items() if k != "op"})


def evaluate(rules: list[dict[str, Any]], answers: dict[str, Any]) -> bool:
    return all(parse(r).interpret(answers) for r in rules)
