"""Plant model REST API."""

from __future__ import annotations

from fastapi import APIRouter

from mes_core.plant_model.composite import PlantTreeNode
from mes_core.plant_model.schemas import PlantNodeCreate, PlantNodeOut, PlantTreeOut
from mes_core.plant_model.service import PlantModelService
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/plant-model", tags=["plant-model"])


def _to_tree_out(node: PlantTreeNode) -> PlantTreeOut:
    return PlantTreeOut(
        id=node.id,
        code=node.code,
        name=node.name,
        level=node.level,
        children=[_to_tree_out(c) for c in node.children],
    )


@router.post("/nodes", response_model=PlantNodeOut, status_code=201)
async def create_node(body: PlantNodeCreate, ctx: ContextDep, session: SessionDep):
    node = await PlantModelService(session).create_node(ctx, body)
    return node


@router.get("/tree", response_model=list[PlantTreeOut])
async def get_tree(ctx: ContextDep, session: SessionDep):
    roots = await PlantModelService(session).get_tree(ctx)
    return [_to_tree_out(r) for r in roots]
