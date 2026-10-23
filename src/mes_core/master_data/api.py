"""Master data REST API."""

from __future__ import annotations

from fastapi import APIRouter

from mes_core.master_data.schemas import (
    MaterialCreate,
    MaterialOut,
    ProductCreate,
    ProductOut,
    RouteCreate,
    RouteOut,
)
from mes_core.master_data.service import MasterDataService
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/master-data", tags=["master-data"])


@router.post("/materials", response_model=MaterialOut, status_code=201)
async def create_material(body: MaterialCreate, ctx: ContextDep, session: SessionDep):
    return await MasterDataService(session).create_material(ctx, body)


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(body: ProductCreate, ctx: ContextDep, session: SessionDep):
    return await MasterDataService(session).create_product(ctx, body)


@router.post("/routes", response_model=RouteOut, status_code=201)
async def create_route(body: RouteCreate, ctx: ContextDep, session: SessionDep):
    return await MasterDataService(session).create_route(ctx, body)


@router.post("/routes/{route_id}/approve", response_model=RouteOut)
async def approve_route(route_id: str, ctx: ContextDep, session: SessionDep):
    return await MasterDataService(session).approve_route(ctx, route_id)
