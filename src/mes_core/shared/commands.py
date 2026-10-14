"""Command pattern (GoF, Behavioral).

Operator actions (start / pause / complete an operation, consume a lot, record
counts) are modeled as command objects executed by an invoker. Benefits:
- a client-generated ``request_id`` makes retries idempotent (NFR: no duplicate
  counts when a terminal retries a queued action);
- commands are uniform, loggable and queueable (offline operator terminals).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from mes_core.shared.context import OperationContext

T = TypeVar("T")


class Command(abc.ABC, Generic[T]):
    """An executable, auditable unit of work."""

    @abc.abstractmethod
    async def execute(self) -> T: ...


@dataclass
class CommandInvoker:
    """Executes commands and remembers results per request id (idempotency)."""

    _seen: dict[str, Any] = field(default_factory=dict)

    async def run(self, command: Command[T], ctx: OperationContext) -> T:
        key = ctx.request_id
        if key is not None and key in self._seen:
            return self._seen[key]  # replay: return prior result, do not re-apply
        result = await command.execute()
        if key is not None:
            self._seen[key] = result
        return result
