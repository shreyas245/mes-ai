"""Production state machines (plan decision 3).

Order:     Created → Released → In Progress ⇄ On Hold → Completed → Closed  (+ Cancelled)
Operation: Pending → Ready → Running ⇄ Paused → Done

Built on the generic ``StateMachine`` (State + Template Method). Transitions are
declared once and reused by the service, which validates every transition in one
place and emits an audit entry + domain event per transition.
"""

from __future__ import annotations

import enum

from mes_core.shared.state_machine import StateMachine


class OrderState(str, enum.Enum):
    CREATED = "created"
    RELEASED = "released"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class OperationState(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    DONE = "done"


def build_order_machine() -> StateMachine[OrderState, object]:
    sm: StateMachine[OrderState, object] = StateMachine()
    (
        sm.allow("release", OrderState.CREATED, OrderState.RELEASED)
        .allow("start", OrderState.RELEASED, OrderState.IN_PROGRESS)
        .allow("hold", OrderState.IN_PROGRESS, OrderState.ON_HOLD)
        .allow("resume", OrderState.ON_HOLD, OrderState.IN_PROGRESS)
        .allow("complete", OrderState.IN_PROGRESS, OrderState.COMPLETED)
        .allow("close", OrderState.COMPLETED, OrderState.CLOSED)
        .allow("cancel", OrderState.CREATED, OrderState.CANCELLED)
        .allow("cancel", OrderState.RELEASED, OrderState.CANCELLED)
        .allow("cancel", OrderState.ON_HOLD, OrderState.CANCELLED)
    )
    return sm


def build_operation_machine() -> StateMachine[OperationState, object]:
    sm: StateMachine[OperationState, object] = StateMachine()
    (
        sm.allow("ready", OperationState.PENDING, OperationState.READY)
        .allow("start", OperationState.READY, OperationState.RUNNING)
        .allow("pause", OperationState.RUNNING, OperationState.PAUSED)
        .allow("resume", OperationState.PAUSED, OperationState.RUNNING)
        .allow("complete", OperationState.RUNNING, OperationState.DONE)
    )
    return sm


ORDER_MACHINE = build_order_machine()
OPERATION_MACHINE = build_operation_machine()
