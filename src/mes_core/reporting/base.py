"""Report generation framework.

Patterns:
- **Template Method** — :class:`ReportGenerator.generate` fixes the algorithm
  (title → collect rows → summarize → render) while each report supplies the
  steps.
- **Strategy** — the output format (text / CSV / future PDF) is a renderer
  strategy injected into the generator.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Report:
    title: str
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


class Renderer(abc.ABC):
    """Output-format strategy."""

    @abc.abstractmethod
    def render(self, report: Report) -> str: ...


class TextRenderer(Renderer):
    def render(self, report: Report) -> str:
        lines = [report.title, "=" * len(report.title)]
        if report.columns:
            lines.append(" | ".join(report.columns))
        for row in report.rows:
            lines.append(" | ".join(str(row.get(c, "")) for c in report.columns))
        if report.summary:
            lines.append("")
            lines.extend(f"{k}: {v}" for k, v in report.summary.items())
        return "\n".join(lines)


class CsvRenderer(Renderer):
    def render(self, report: Report) -> str:
        import csv
        import io

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=report.columns)
        writer.writeheader()
        for row in report.rows:
            writer.writerow({c: row.get(c, "") for c in report.columns})
        return buf.getvalue()


class ReportGenerator(abc.ABC):
    """Template Method: fixed pipeline, overridable steps."""

    def __init__(self, renderer: Renderer | None = None) -> None:
        self.renderer = renderer or TextRenderer()

    async def generate(self) -> str:
        report = Report(title=self.title())
        report.columns = self.columns()
        report.rows = await self.collect_rows()
        report.summary = self.summarize(report.rows)
        return self.renderer.render(report)

    @abc.abstractmethod
    def title(self) -> str: ...

    @abc.abstractmethod
    def columns(self) -> list[str]: ...

    @abc.abstractmethod
    async def collect_rows(self) -> list[dict[str, Any]]: ...

    def summarize(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {"row_count": len(rows)}
