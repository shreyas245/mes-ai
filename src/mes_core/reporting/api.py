"""Reporting REST API."""

from __future__ import annotations

from fastapi import APIRouter, Response

from mes_core.reporting.base import CsvRenderer, TextRenderer
from mes_core.reporting.reports import OeeReport, OrderSummaryReport
from mes_core.shared.deps import ContextDep, SessionDep

router = APIRouter(prefix="/reporting", tags=["reporting"])


def _renderer(fmt: str):
    return CsvRenderer() if fmt == "csv" else TextRenderer()


@router.get("/order-summary")
async def order_summary(ctx: ContextDep, session: SessionDep, format: str = "text"):
    report = OrderSummaryReport(session, ctx.site_id, _renderer(format))
    body = await report.generate()
    media = "text/csv" if format == "csv" else "text/plain"
    return Response(content=body, media_type=media)


@router.get("/oee")
async def oee_report(ctx: ContextDep, session: SessionDep, format: str = "text"):
    report = OeeReport(session, ctx.site_id, _renderer(format))
    body = await report.generate()
    media = "text/csv" if format == "csv" else "text/plain"
    return Response(content=body, media_type=media)
