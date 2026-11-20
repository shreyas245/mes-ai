"""Tag map: raw tag path → (equipment_id, meaning).

Loaded from the plant_model ``tag_mapping`` table (pushed to the edge as config)
so the gateway can attribute each reading to an equipment node and a meaning.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class TagBinding:
    equipment_id: str
    meaning: str
    unit: str | None = None


@dataclass
class TagMap:
    bindings: dict[str, TagBinding] = field(default_factory=dict)

    def add(self, tag_path: str, binding: TagBinding) -> None:
        self.bindings[tag_path] = binding

    def resolve(self, tag_path: str) -> TagBinding | None:
        return self.bindings.get(tag_path)

    def tags(self) -> list[str]:
        return list(self.bindings)
