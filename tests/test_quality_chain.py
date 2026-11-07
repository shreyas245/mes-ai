"""Chain of Responsibility: in-process inspection checks."""

from __future__ import annotations

from mes_core.quality.checks import Measurement, inspect


def test_within_spec_passes():
    assert inspect(Measurement("weight", 100.0, lower=98.0, upper=102.0)).ok


def test_below_lower_limit_fails():
    result = inspect(Measurement("weight", 97.0, lower=98.0, upper=102.0))
    assert not result.ok
    assert "LSL" in result.message


def test_missing_value_fails_first():
    result = inspect(Measurement("weight", None, lower=98.0, upper=102.0))
    assert not result.ok
    assert "required" in result.message
