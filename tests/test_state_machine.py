"""State pattern: order/operation transitions are validated in one place."""

from __future__ import annotations

import pytest

from mes_core.production.states import (
    ORDER_MACHINE,
    OperationState,
    OrderState,
    build_operation_machine,
)
from mes_core.shared.state_machine import IllegalTransition


def test_order_happy_path():
    state = OrderState.CREATED
    for trigger, expected in [
        ("release", OrderState.RELEASED),
        ("start", OrderState.IN_PROGRESS),
        ("hold", OrderState.ON_HOLD),
        ("resume", OrderState.IN_PROGRESS),
        ("complete", OrderState.COMPLETED),
        ("close", OrderState.CLOSED),
    ]:
        state = ORDER_MACHINE.next_state(trigger, state, object())
        assert state is expected


def test_illegal_order_transition_rejected():
    with pytest.raises(IllegalTransition):
        ORDER_MACHINE.next_state("complete", OrderState.CREATED, object())


def test_operation_machine():
    sm = build_operation_machine()
    assert sm.next_state("start", OperationState.READY, object()) is OperationState.RUNNING
    with pytest.raises(IllegalTransition):
        sm.next_state("complete", OperationState.PAUSED, object())
