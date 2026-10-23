"""Master data repositories."""

from __future__ import annotations

from mes_core.master_data.models import (
    BomItem,
    MaterialDefinition,
    Product,
    Route,
    RouteStep,
    StepForm,
)
from mes_core.shared.repository import SqlAlchemyRepository


class MaterialRepository(SqlAlchemyRepository[MaterialDefinition]):
    model = MaterialDefinition


class BomItemRepository(SqlAlchemyRepository[BomItem]):
    model = BomItem


class ProductRepository(SqlAlchemyRepository[Product]):
    model = Product


class RouteRepository(SqlAlchemyRepository[Route]):
    model = Route


class RouteStepRepository(SqlAlchemyRepository[RouteStep]):
    model = RouteStep


class StepFormRepository(SqlAlchemyRepository[StepForm]):
    model = StepForm
