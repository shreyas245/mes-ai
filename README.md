# mes-ai — an open Manufacturing Execution System

An open MES built on open standards (ISA-95, ISA-88, OPC UA, MQTT/Sparkplug B, B2MML).

- Architecture: [documentation/architecture-plan.md](documentation/architecture-plan.md)
- Design patterns (GoF) map: [documentation/design-patterns.md](documentation/design-patterns.md)
- User stories: [documentation/user-stories.md](documentation/user-stories.md)

## Layout

```
src/mes_core/        FastAPI modular monolith
  shared/            DB, ISA-95 base types, state machine, outbox, audit, RBAC, bus
  plant_model/       ISA-95 equipment hierarchy + tag mapping   (Composite, Visitor)
  master_data/       materials, BOMs, products, versioned routes (Builder, Prototype)
  production/        orders + operations state machines          (State, Command)
  genealogy/         material lots + forward/backward trace      (Visitor)
  performance/       OEE, downtime, reason codes                 (Strategy, Observer)
  quality/           inspections, SPC, nonconformances           (Chain of Resp., Strategy)
  compliance/        hash-chained audit viewer + e-signatures    (Memento, Facade)
  reporting/         shift / order / OEE reports                 (Template Method, Strategy)
  material/          locations, inventory, kitting               (Phase 2, scaffold)
  workflow/          versioned forms + rules DSL                 (Interpreter, Phase 2)
  integration/       ERP / B2MML adapters                        (Adapter, Phase 2)
src/edge_gateway/    plant-floor connectors + store-and-forward  (Abstract Factory, Proxy)
src/simulator/       virtual bottling line with injected faults  (Strategy, Decorator)
migrations/          Alembic
deploy/compose/      docker-compose for local dev
deploy/helm/mes/     Helm chart (scaffold)
web/                 React front-end (scaffold)
tests/               unit + integration + HTTP e2e
```

## Quick start (dev)

```bash
uv sync --extra dev
```

Run the API (SQLite by default, tables auto-created in dev):

```bash
uv run mes-core
```

Open http://localhost:8000/docs for the OpenAPI UI, and `GET /health` to check.

Run the tests:

```bash
uv run pytest -q
```

Run the line simulator standalone:

```bash
uv run python -m simulator.main
```

## Full stack (Postgres/Timescale + NATS + Redis + Keycloak)

```bash
docker compose -f deploy/compose/docker-compose.yml up --build
```

Set `MES_DATABASE_URL` to the async Postgres URL to use Postgres instead of the
SQLite dev default (see `src/mes_core/config.py` for all `MES_*` settings).

## Design notes

- **Modular monolith**: one app, strict module boundaries — each module owns its
  tables and exposes a service Facade; no cross-module table access.
- **Every state change is auditable**: transitions go through the shared state
  machine, write a hash-chained audit entry and enqueue a domain event in the
  same transaction (transactional outbox).
- **Operator actions are idempotent**: commands carry a client `X-Request-Id`, so
  a retried shop-floor action never double-counts.
- **The edge is separate from day one**: it buffers to SQLite and replays in order
  after a network outage.
