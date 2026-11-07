"""In-process quality checks (Chain of Responsibility).

A measurement passes through a chain of checks (required, numeric, within spec
limits). A failed check can block the operation. The chain is assembled per
characteristic from its spec limits.
"""

from __future__ import annotations

from dataclasses import dataclass

from mes_core.shared.chain import CheckResult, Handler, build_chain


@dataclass(slots=True)
class Measurement:
    characteristic: str
    value: float | None
    lower: float | None = None
    upper: float | None = None


class RequiredCheck(Handler[Measurement]):
    def check(self, request: Measurement) -> CheckResult:
        if request.value is None:
            return CheckResult.failed(f"{request.characteristic}: value required")
        return CheckResult.passed()


class LowerLimitCheck(Handler[Measurement]):
    def check(self, request: Measurement) -> CheckResult:
        if request.lower is not None and request.value is not None:
            if request.value < request.lower:
                return CheckResult.failed(
                    f"{request.characteristic}: {request.value} < LSL {request.lower}"
                )
        return CheckResult.passed()


class UpperLimitCheck(Handler[Measurement]):
    def check(self, request: Measurement) -> CheckResult:
        if request.upper is not None and request.value is not None:
            if request.value > request.upper:
                return CheckResult.failed(
                    f"{request.characteristic}: {request.value} > USL {request.upper}"
                )
        return CheckResult.passed()


def inspect(measurement: Measurement) -> CheckResult:
    chain = build_chain(RequiredCheck(), LowerLimitCheck(), UpperLimitCheck())
    return chain.handle(measurement)
