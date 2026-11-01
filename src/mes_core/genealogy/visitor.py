"""Genealogy traversal (Visitor + Iterator over a lot graph).

Forward trace: given a lot, find everything produced from it (children,
grandchildren…). Backward trace: find everything that went into it (parents…).
Implemented with recursive CTEs in the service; this module provides the
in-memory graph and a Visitor used to shape trace reports.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field


@dataclass
class LotNode:
    lot_id: str
    lot_code: str
    children: list["LotNode"] = field(default_factory=list)

    def accept(self, visitor: "LotVisitor", depth: int = 0) -> None:
        visitor.visit(self, depth)
        for child in self.children:
            child.accept(visitor, depth + 1)


class LotVisitor(abc.ABC):
    @abc.abstractmethod
    def visit(self, node: LotNode, depth: int) -> None: ...


class FlattenVisitor(LotVisitor):
    """Collect (depth, lot_code) pairs for a flat trace report."""

    def __init__(self) -> None:
        self.rows: list[tuple[int, str]] = []

    def visit(self, node: LotNode, depth: int) -> None:
        self.rows.append((depth, node.lot_code))
