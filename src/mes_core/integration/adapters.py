"""ERP integration adapters (Adapter pattern, GoF Structural). Plan: Phase 2.

The MES speaks one internal ``OrderImport`` shape. Each ERP (B2MML/XML, SAP
IDoc/OData, CSV) has its own format; an adapter converts that external format to
the internal shape, so the production module never knows which ERP it came from.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OrderImport:
    """Internal canonical order shape used by the production module."""

    order_no: str
    product_code: str
    quantity: float


class ErpAdapter(abc.ABC):
    """Target interface the MES expects."""

    @abc.abstractmethod
    def to_orders(self, raw: object) -> list[OrderImport]: ...


class B2mmlAdapter(ErpAdapter):
    """Adapts B2MML (ISA-95 XML) ``ProductionRequest`` elements."""

    def to_orders(self, raw: object) -> list[OrderImport]:
        # raw: parsed list of dicts from B2MML <ProductionRequest> elements.
        orders: list[OrderImport] = []
        for pr in raw or []:  # type: ignore[union-attr]
            orders.append(
                OrderImport(
                    order_no=pr["ID"],
                    product_code=pr["SegmentRequirement"]["MaterialProducedRequirement"]["MaterialDefinitionID"],
                    quantity=float(pr["SegmentRequirement"]["MaterialProducedRequirement"]["Quantity"]),
                )
            )
        return orders


class CsvErpAdapter(ErpAdapter):
    """Adapts a simple CSV export: order_no, product_code, quantity."""

    def to_orders(self, raw: object) -> list[OrderImport]:
        import csv
        import io

        reader = csv.DictReader(io.StringIO(str(raw)))
        return [
            OrderImport(
                order_no=r["order_no"],
                product_code=r["product_code"],
                quantity=float(r["quantity"]),
            )
            for r in reader
        ]
