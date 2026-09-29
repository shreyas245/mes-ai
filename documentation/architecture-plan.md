# Architecture Plan — an open MES modeled on FactoryTalk MES

## Context

Goal: build a Manufacturing Execution System with the functional scope of Rockwell
**FactoryTalk MES** (FactoryTalk ProductionCentre / PharmaSuite, Metrics, Batch, Logistics,
Historian). It is a functional clone, not a copy: no Rockwell code, branding, file formats or
trademarks. Everything is built on open standards (ISA-95, ISA-88, OPC UA, MQTT/Sparkplug B,
B2MML) so it can work alongside any PLC or ERP, not only Allen-Bradley and SAP.

Starting point: the repo holds a Python 3.14 / FastAPI / `uv` skeleton, so the backend stays
Python.

### What FactoryTalk MES does, and what we will build for each part

| FactoryTalk capability | Our module | MVP? |
|---|---|---|
| Plant model (enterprise → site → area → line → work cell → equipment) | `plant-model` | ✅ |
| Product definitions, BOMs, routings, operations | `master-data` | ✅ |
| Production orders, dispatching, WIP tracking (ProductionCentre) | `production` | ✅ |
| Shop-floor operator screens, electronic work instructions | `shopfloor-ui` | ✅ |
| Machine data collection, tags, events (FT Linx / Gateway) | `edge-gateway` | ✅ |
| OEE, downtime, reason codes (FactoryTalk Metrics) | `performance` | ✅ |
| Inspections, SPC, nonconformance (Quality) | `quality` | ✅ (basic) |
| Lot/serial genealogy, track & trace | `genealogy` | ✅ |
| Material, inventory, kitting, consumption (FT Logistics) | `material` | Phase 2 |
| Electronic batch records, recipes (PharmaSuite, FT Batch / ISA-88) | `batch` | Phase 3 |
| Configurable workflows and forms (Process Designer) | `workflow` | Phase 2 |
| Electronic signatures and audit trail (21 CFR Part 11) | `compliance` | ✅ (audit), Phase 2 (e-sig) |
| Time-series history (FT Historian) | TimescaleDB | ✅ |
| Reports and dashboards (FT VantagePoint / Analytics) | `reporting` | ✅ (basic) |
| ERP integration (SAP, Oracle, Dynamics) | `integration` | Phase 2 |
| Finite scheduling (FT Scheduler) | `scheduling` | Phase 3 |
| AI copilot over MES data and SOPs | `copilot` | Phase 4 |

## Architecture

```
                                    ┌──────────────────────────────────────────────┐
 Users                              │                 Web clients (React)            │
 ─────                              │  Operator terminal │ Supervisor │ Engineer/Admin│
 operators, supervisors,            │  (tablet, kiosk)   │ dashboards │ modelers      │
 quality, engineers                 └───────────────┬────────────────────────────────┘
                                                    │ HTTPS (REST + WebSocket)
                                    ┌───────────────▼────────────────────────────────┐
                                    │  API gateway / auth  (Keycloak OIDC, RBAC)      │
                                    └───────────────┬────────────────────────────────┘
                                                    │
        ┌───────────────────────────────────────────▼─────────────────────────────────┐
        │                     mes-core  (FastAPI, modular monolith)                    │
        │                                                                              │
        │  plant-model  master-data  production  performance  quality  genealogy      │
        │  material     workflow     compliance  reporting    integration             │
        │                                                                              │
        │  shared kernel: ISA-95 entities · state machines · audit log · outbox       │
        └──────┬──────────────────────────┬───────────────────────────┬───────────────┘
               │ SQL                      │ publish / subscribe       │ jobs
        ┌──────▼──────────┐       ┌───────▼─────────┐        ┌────────▼──────────┐
        │ PostgreSQL       │       │ NATS JetStream  │        │ workers (Arq +    │
        │ + TimescaleDB    │       │ (event bus)     │        │ Redis): reports,  │
        │ transactional +  │       └───────▲─────────┘        │ OEE rollups, ERP  │
        │ time-series      │               │                  │ sync              │
        └──────────────────┘               │ machine events, tag values
                                    ┌──────┴────────────────────────────┐
                                    │ edge-gateway (one per plant/line)  │
                                    │ OPC UA client · MQTT Sparkplug B · │
                                    │ Modbus · store-and-forward buffer  │
                                    └──────▲────────────────────────────┘
                                           │
                                 PLCs, machines, scanners, scales
                                 (simulator for dev and demos)

 Observability: OpenTelemetry → Prometheus + Grafana, Loki (logs), Tempo (traces)
```

### Key design decisions

1. **Modular monolith first, not microservices.** One FastAPI app (`mes-core`) with strict
   module boundaries (each module owns its tables and exposes a Python service interface; no
   cross-module table access). This keeps transactions simple (starting an operation, consuming
   material and writing genealogy happens in one DB transaction) and is realistic for a small
   team. Modules can be split out later along these boundaries. Only the **edge gateway** is
   separate from day one, because it runs on the plant floor next to the machines.

2. **ISA-95 as the data model.** Every table maps to an ISA-95 Part 2/4 object: equipment
   hierarchy, material definition/lot/sublot, product definition and segments, operations
   request/schedule (orders), operations performance (actuals), personnel. This makes ERP
   integration via B2MML straightforward and keeps vocabulary familiar to MES engineers.

3. **Explicit state machines for orders and operations.** Production order:
   `Created → Released → In Progress ⇄ On Hold → Completed → Closed` (plus `Cancelled`).
   Operation/step: `Pending → Ready → Running ⇄ Paused → Done`. Transitions are validated in
   one place, each one is an audit event, and each one publishes a domain event on the bus.

4. **Event-driven, with a transactional outbox.** Domain events (`OrderReleased`,
   `OperationStarted`, `MaterialConsumed`, `MachineStateChanged`, `InspectionFailed`) are written
   to an outbox table in the same transaction as the change, then relayed to NATS. Consumers
   (OEE engine, reporting, integrations, later the AI copilot) never miss or double-apply
   events.

5. **Edge gateway with store-and-forward.** Plants lose network. The gateway buffers tag
   values and machine events locally (SQLite) and replays them in order when the link comes
   back. It reads via OPC UA (`asyncua`) and MQTT Sparkplug B, maps raw tags to equipment
   through a configurable tag map, and derives machine states (Running / Idle / Down / Blocked /
   Starved) from tag rules.

6. **Configurable, not hard-coded, workflows (Phase 2).** FactoryTalk's strength is the Process
   Designer, where engineers model routes, steps and forms without code. Our version: routes and
   step forms are stored as versioned JSON definitions (JSON Schema for data-entry forms, a
   small rules DSL for checks like "weight within ±2 %"). Definitions go through
   *Draft → Approved → Effective*, so production always runs against an approved version.

7. **Compliance built in from the start.** An append-only `audit_log` table (who, what, when,
   old/new values, reason), protected by DB triggers and a hash chain so tampering is
   detectable. Electronic signatures (re-authentication plus meaning: "performed by",
   "verified by") are added in Phase 2 for GxP customers.

8. **Multi-site, single-tenant deployment.** MES is usually installed per company, often
   on-prem. Design for one deployment per customer with many sites; every record carries
   `site_id` and access is filtered by the user's site/area roles.

### Technology stack

| Layer | Choice |
|---|---|
| Backend | Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic |
| Database | PostgreSQL 17 + TimescaleDB (machine data, OEE rollups) |
| Event bus | NATS JetStream |
| Background jobs | Arq + Redis |
| Edge | Python `asyncua`, `paho-mqtt` + Sparkplug B protobufs, SQLite buffer |
| Auth | Keycloak (OIDC), RBAC by role + site/area scope |
| Frontend | React + TypeScript + Vite, TanStack Query, shadcn/ui, ECharts |
| Real-time UI | WebSockets (order status, machine state, andon) |
| Deployment | docker compose (dev), Kubernetes + Helm (production), plain VM install option |
| Observability | OpenTelemetry, Prometheus, Grafana, Loki |
| Testing | pytest, testcontainers (Postgres, NATS), Playwright (UI), k6 (load) |

## Core data model (MVP subset)

```
site ─< area ─< line ─< work_center ─< equipment
                                        └─< tag_mapping (tag → equipment + meaning)

material_definition ─< bom_item
product ─< route (versioned) ─< route_step ─> work_center
                                     └─< step_form (data collection definition)

production_order ─> product, route_version, line
   └─< order_operation (state machine) ─< operation_execution (actual start/stop, operator)
         ├─< material_consumption ─> material_lot
         ├─< production_output   ─> material_lot (produced lot / serial)
         └─< data_collection_value (form answers, measurements)

material_lot ─< genealogy_link (parent lot → child lot)

machine_state_event (hypertable)   downtime_event ─> reason_code (tree)
tag_value (hypertable)             oee_rollup (hypertable, per equipment per 15 min / shift)
shift_calendar ─< shift

inspection_plan ─< characteristic (spec limits)
inspection_result ─< measurement      nonconformance ─> lot / order

app_user ─< role_assignment (role, site/area scope)
audit_log (append-only, hash-chained)    outbox_event
```

## Repo layout

```
src/mes_core/              FastAPI app (modular monolith)
  plant_model/             each module: api.py, service.py, models.py, schemas.py, events.py
  master_data/
  production/
  performance/             OEE engine, downtime, reason codes
  quality/
  genealogy/
  material/                (phase 2)
  workflow/                (phase 2)
  compliance/              audit log, e-signatures
  reporting/
  integration/             ERP / B2MML adapters (phase 2)
  shared/                  db session, ISA-95 base types, state machine, outbox, auth
src/edge_gateway/          OPC UA / MQTT connectors, tag mapping, store-and-forward
src/simulator/             virtual packaging line (OPC UA server + MQTT) with injected faults
web/                       React app: operator terminal, supervisor, admin/modeling
migrations/                Alembic
deploy/
  compose/                 docker-compose for local dev
  helm/mes/                Helm chart
tests/                     unit, integration (testcontainers), e2e
documentation/
learn/                     scratch experiments (existing)
```

## Build phases

### Phase 1 — Foundation and plant model (weeks 1–3)
- docker compose: Postgres + Timescale, NATS, Redis, Keycloak.
- `shared` kernel: DB session, Alembic, outbox relay, audit log, generic state machine,
  Keycloak auth with site-scoped RBAC.
- `plant_model` and `master_data` CRUD (sites → equipment, materials, products, BOMs, routes).
- Admin UI to build the equipment tree and routes.

### Phase 2 — Production execution (weeks 4–7)
- `production`: create/import orders, release to line, dispatch list per work center.
- Operator terminal: log in at a station, pick an order, start/pause/complete operations,
  record good/scrap counts, fill step forms, scan lots for consumption.
- `genealogy`: produced lots/serials linked to consumed lots; forward and backward trace
  queries (recursive CTE).
- Real-time order status over WebSocket.

### Phase 3 — Machine connectivity and performance (weeks 8–10)
- `simulator`: a bottling line (filler, capper, labeler) over OPC UA and MQTT, with jams,
  micro-stops and speed losses.
- `edge_gateway`: tag mapping, machine state derivation, store-and-forward, publish to NATS.
- `performance`: downtime events with operator reason-coding, OEE (availability × performance
  × quality) per equipment/shift, Timescale continuous aggregates, andon board and OEE
  dashboards.

### Phase 4 — Quality and compliance (weeks 11–13)
- `quality`: inspection plans tied to route steps, in-process checks that can block an
  operation, SPC charts (X̄-R, I-MR) with Western Electric rules, nonconformance records with
  lot hold/release.
- `compliance`: hash-chained audit trail viewer, electronic signatures on critical
  transitions.
- Reports: shift report, order summary, genealogy report (PDF export).

### Later phases
- **Material & logistics:** locations, inventory, kitting, line-side replenishment.
- **Workflow designer:** versioned visual route/form designer with approval cycle.
- **ERP integration:** B2MML import of orders and materials, export of confirmations;
  SAP (IDoc/OData) adapter.
- **Batch / EBR (ISA-88):** recipes, phases, electronic batch record, review by exception.
- **Scheduling:** finite-capacity scheduling with a Gantt view.
- **AI copilot:** RAG over SOPs plus read-only tools over MES data, consuming the same event
  stream (see [user-stories.md](user-stories.md)).

## Non-functional requirements

- **Availability:** shop floor must keep running during a central outage → edge buffering,
  and operator terminals retry queued actions idempotently (client-generated request IDs).
- **Latency:** operator actions < 300 ms p95; machine state visible on dashboards < 2 s.
- **Throughput target (MVP):** 50 lines × 200 tags at 1 Hz = 10 k tag values/s into Timescale.
- **Data integrity:** all execution actions are transactional; no lost or duplicated counts.
- **Security:** OIDC everywhere, least-privilege roles, TLS between edge and core, secrets
  outside the repo.
- **Traceability:** every change to orders, lots, quality records and master data is in the
  audit log.

## Verification

- `docker compose up` brings up the full stack plus the simulator; the OEE dashboard shows the
  simulated line within a minute.
- End-to-end scenario test (Playwright + API): create product and route → create and release
  an order → operator starts the operation, consumes lot `L-100`, produces lot `L-200` →
  simulator injects a labeler jam → operator assigns a downtime reason → inspection fails and
  places `L-200` on hold → genealogy trace from `L-100` finds `L-200` → audit log shows every
  step.
- Integration tests with testcontainers for the state machines, outbox delivery and OEE math
  (known simulator inputs → expected OEE values).
- Kill the network between edge gateway and core for 5 minutes; after reconnect, no tag values
  or machine events are missing.
- k6 load test at the target tag rate and 100 concurrent operator terminals.
