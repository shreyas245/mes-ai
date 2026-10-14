"""Command pattern: retried operator actions are idempotent via request_id."""

from __future__ import annotations

from mes_core.shared.commands import Command, CommandInvoker
from tests.conftest import make_ctx


class _Counter(Command[int]):
    def __init__(self) -> None:
        self.calls = 0

    async def execute(self) -> int:
        self.calls += 1
        return self.calls


async def test_same_request_id_runs_once():
    invoker = CommandInvoker()
    ctx = make_ctx(request_id="req-1")
    cmd = _Counter()
    first = await invoker.run(cmd, ctx)
    second = await invoker.run(cmd, ctx)  # retry
    assert first == second == 1
    assert cmd.calls == 1
