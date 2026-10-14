"""Chain of Responsibility (GoF, Behavioral).

Used for validation/authorization pipelines: RBAC checks, in-process quality
checks that can block an operation, and form-field rule evaluation. Each handler
either passes the request to the next handler or rejects it.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Generic, TypeVar

R = TypeVar("R")


@dataclass(slots=True)
class CheckResult:
    ok: bool
    message: str = ""

    @classmethod
    def passed(cls) -> CheckResult:
        return cls(True)

    @classmethod
    def failed(cls, message: str) -> CheckResult:
        return cls(False, message)


class Handler(abc.ABC, Generic[R]):
    """A link in the chain."""

    def __init__(self) -> None:
        self._next: Handler[R] | None = None

    def set_next(self, nxt: Handler[R]) -> Handler[R]:
        self._next = nxt
        return nxt  # enables fluent chaining: a.set_next(b).set_next(c)

    def handle(self, request: R) -> CheckResult:
        result = self.check(request)
        if not result.ok:
            return result
        if self._next is not None:
            return self._next.handle(request)
        return CheckResult.passed()

    @abc.abstractmethod
    def check(self, request: R) -> CheckResult: ...


def build_chain(*handlers: Handler[R]) -> Handler[R]:
    """Link handlers in order and return the head."""
    for a, b in zip(handlers, handlers[1:]):
        a.set_next(b)
    return handlers[0]
