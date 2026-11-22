"""Virtual bottling line: filler → capper → labeler (plan Phase 3).

Each station ticks once per cycle, producing tag values and applying any injected
faults. The line emits readings that an edge gateway (or a test) can consume to
exercise OEE, downtime reason-coding and andon end to end.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from simulator.faults import Fault, StationTick


@dataclass
class Station:
    name: str
    nominal_speed: float = 60.0  # units/min
    faults: list[Fault] = field(default_factory=list)
    total_produced: int = 0

    def tick(self) -> StationTick:
        per_tick = int(self.nominal_speed / 60)  # 1-second tick
        result = StationTick(running=True, speed=self.nominal_speed, produced=max(per_tick, 1))
        for fault in self.faults:
            result = fault.apply(result)
        self.total_produced += result.produced
        return result


@dataclass
class BottlingLine:
    stations: list[Station] = field(default_factory=list)

    @classmethod
    def default(cls) -> "BottlingLine":
        return cls(
            stations=[
                Station("filler"),
                Station("capper"),
                Station("labeler"),
            ]
        )

    def tick(self) -> dict[str, StationTick]:
        """Advance every station one cycle; return per-station tags."""
        return {s.name: s.tick() for s in self.stations}

    def readings(self) -> dict[str, dict[str, float | bool | str]]:
        """Flatten a tick into tag-path → value readings for the gateway."""
        out: dict[str, dict[str, float | bool | str]] = {}
        for name, tick in self.tick().items():
            out[name] = {
                "speed": tick.speed,
                "good_count": tick.produced,
                "fault": tick.fault or "",
                "running": tick.running,
            }
        return out
