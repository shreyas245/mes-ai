"""Composite pattern (GoF, Structural) over the plant hierarchy.

A site, area, line, work center and equipment are treated uniformly as tree
nodes. ``accept`` enables the **Visitor** pattern for rollups (e.g. count
equipment, aggregate OEE) without the traversal logic leaking into callers.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field

from mes_core.plant_model.models import PlantLevel, PlantNode


class NodeVisitor(abc.ABC):
    """Visitor over the plant tree."""

    @abc.abstractmethod
    def visit(self, node: "PlantTreeNode") -> None: ...


@dataclass
class PlantTreeNode:
    """In-memory composite node (leaf and branch treated the same)."""

    id: str
    code: str
    name: str
    level: PlantLevel
    children: list["PlantTreeNode"] = field(default_factory=list)

    def add(self, child: "PlantTreeNode") -> "PlantTreeNode":
        self.children.append(child)
        return child

    def accept(self, visitor: NodeVisitor) -> None:
        visitor.visit(self)
        for child in self.children:
            child.accept(visitor)

    def descendants(self) -> list["PlantTreeNode"]:
        out: list[PlantTreeNode] = []
        for child in self.children:
            out.append(child)
            out.extend(child.descendants())
        return out


def build_tree(rows: list[PlantNode]) -> list[PlantTreeNode]:
    """Assemble composite roots from a flat list of ORM rows."""
    nodes = {
        r.id: PlantTreeNode(r.id, r.code, r.name, r.level) for r in rows
    }
    roots: list[PlantTreeNode] = []
    for r in rows:
        node = nodes[r.id]
        if r.parent_id and r.parent_id in nodes:
            nodes[r.parent_id].add(node)
        else:
            roots.append(node)
    return roots


class EquipmentCounter(NodeVisitor):
    """Example Visitor: count equipment-level leaves under a subtree."""

    def __init__(self) -> None:
        self.count = 0

    def visit(self, node: PlantTreeNode) -> None:
        if node.level is PlantLevel.EQUIPMENT:
            self.count += 1
