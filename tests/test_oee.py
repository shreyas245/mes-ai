"""Strategy pattern: OEE math with known inputs → expected values."""

from __future__ import annotations

from mes_core.performance.oee import OeeCalculator, OeeInputs


def test_oee_known_values():
    # 8h planned, 7h run, ideal 1s/unit, 25200 total, 24000 good.
    inputs = OeeInputs(
        planned_time_s=8 * 3600,
        run_time_s=7 * 3600,
        ideal_cycle_time_s=1.0,
        total_count=25200,
        good_count=24000,
    )
    result = OeeCalculator().calculate(inputs)
    assert round(result.availability, 4) == 0.875  # 7/8
    assert round(result.performance, 4) == 1.0     # 1*25200 / 25200
    assert round(result.quality, 4) == round(24000 / 25200, 4)
    assert 0.0 <= result.oee <= 1.0


def test_oee_handles_zero_division():
    inputs = OeeInputs(0, 0, 0, 0, 0)
    result = OeeCalculator().calculate(inputs)
    assert result.oee == 0.0
