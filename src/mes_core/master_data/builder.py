"""Builders for complex master-data aggregates.

Pattern: **Builder** (GoF, Creational). A route with ordered steps and forms is a
multi-part aggregate; the builder assembles it step-by-step with a fluent API and
hands back a ready-to-persist set of objects. Also used to clone a route into a
new version (**Prototype**).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from mes_core.master_data.models import Route, RouteStatus, RouteStep, StepForm


@dataclass
class RouteDraft:
    route: Route
    steps: list[RouteStep] = field(default_factory=list)
    forms: list[StepForm] = field(default_factory=list)


class RouteBuilder:
    """Fluent builder for a route and its steps/forms."""

    def __init__(self, *, site_id: str, product_id: str, version: int = 1) -> None:
        # Generate the id eagerly so child steps/forms can reference it before
        # the row is flushed (the column default only fires at INSERT time).
        self._route = Route(
            id=str(uuid.uuid4()),
            site_id=site_id,
            product_id=product_id,
            version=version,
            status=RouteStatus.DRAFT,
        )
        self._steps: list[RouteStep] = []
        self._forms: list[StepForm] = []

    def step(
        self, *, name: str, work_center_id: str | None = None,
        schema_json: str = "{}", rules_json: str = "[]",
    ) -> "RouteBuilder":
        seq = len(self._steps) + 1
        step = RouteStep(
            id=str(uuid.uuid4()),
            site_id=self._route.site_id,
            route_id=self._route.id,
            sequence=seq,
            name=name,
            work_center_id=work_center_id,
        )
        self._steps.append(step)
        self._forms.append(
            StepForm(
                site_id=self._route.site_id,
                route_step_id=step.id,
                schema_json=schema_json,
                rules_json=rules_json,
            )
        )
        return self

    def build(self) -> RouteDraft:
        return RouteDraft(self._route, self._steps, self._forms)

    @classmethod
    def clone_as_new_version(
        cls, source: RouteDraft, *, new_version: int
    ) -> "RouteBuilder":
        """Prototype: copy an existing route into a fresh draft version."""
        builder = cls(
            site_id=source.route.site_id,
            product_id=source.route.product_id,
            version=new_version,
        )
        for step in sorted(source.steps, key=lambda s: s.sequence):
            form = next(
                (f for f in source.forms if f.route_step_id == step.id), None
            )
            builder.step(
                name=step.name,
                work_center_id=step.work_center_id,
                schema_json=form.schema_json if form else "{}",
                rules_json=form.rules_json if form else "[]",
            )
        return builder
