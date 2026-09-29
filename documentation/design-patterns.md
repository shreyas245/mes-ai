# Design patterns map (Gang of Four)

This codebase applies GoF patterns deliberately. Each is used where it earns its
keep — not for decoration. This document is the index; the patterns are also
named in the docstring of every file that implements them.

## Creational

| Pattern | Where | Why |
|---|---|---|
| **Singleton** | `config.get_settings`, `shared/db.py` (engine, session factory), `shared/event_bus.get_event_bus` | One process-wide settings / engine / bus; cached via `lru_cache` for thread-safety and testability. |
| **Factory Method** | `shared/events.build_event`, `shared/db.session_factory`, `edge_gateway/connectors/factory.py` | Rebuild typed events from stored name+payload; manufacture sessions; build the right protocol connector from config. |
| **Abstract Factory** | `edge_gateway/connectors/factory.py` | A family of `Connector` implementations (OPC UA / MQTT / Modbus) behind one creation point; new protocols register, callers don't change. |
| **Builder** | `master_data/builder.py` (`RouteBuilder`) | Assemble a route + ordered steps + forms step-by-step with a fluent API. |
| **Prototype** | `master_data/builder.RouteBuilder.clone_as_new_version` | Clone an approved route into a new draft version. |

## Structural

| Pattern | Where | Why |
|---|---|---|
| **Composite** | `plant_model/composite.py` (plant tree), `performance` reason-code tree, `master_data` BOM | Treat site/area/line/work-center/equipment (and reason categories) uniformly. |
| **Adapter** | `integration/adapters.py` (`B2mmlAdapter`, `CsvErpAdapter`) | Convert each ERP's external format to the MES's internal `OrderImport`. |
| **Proxy** | `shared/event_bus.BufferedBusProxy`, `edge_gateway/buffer.StoreAndForwardPublisher` | Stand in for the real publisher and add store-and-forward when the link is down. |
| **Decorator** | `shared/service` (audit wrapping), `simulator/faults.py` (faults wrap a station tick) | Add behavior (auditing, fault perturbation) without changing the core object. |
| **Facade** | every module's `service.py` | A module's service is its only public surface; modules never touch each other's tables (plan decision 1). |

## Behavioral

| Pattern | Where | Why |
|---|---|---|
| **State** | `shared/state_machine.py` + `production/states.py` | Order / operation transitions declared per state, validated in one place (plan decision 3). |
| **Template Method** | `shared/service.DomainService._record`, `shared/base_models`, `reporting/base.ReportGenerator`, `shared/state_machine.next_state` | Fix the algorithm, let concretes fill steps. |
| **Strategy** | `performance/oee.py` (OEE factors), `edge_gateway/state_derivation.py` (machine-state rules), `quality/spc.py` (Western Electric rules), `reporting/base` renderers, event-bus transport | Swap policy without touching the engine. |
| **Observer** | `shared/event_bus.InProcessEventBus`, `shared/registry`, `performance/subscribers.py` | Consumers subscribe to domain events; publishers don't know them. |
| **Mediator** | `shared/event_bus` + `shared/registry` | The bus decouples modules; they communicate via events, not direct calls. |
| **Command** | `shared/commands.py` + `production/commands.py` | Operator actions are uniform, idempotent (via `request_id`), queueable for offline terminals. |
| **Chain of Responsibility** | `shared/chain.py`, `shared/rbac.py`, `quality/checks.py` | Validation / authorization pipelines; a failed link stops the chain. |
| **Visitor** | `plant_model/composite` (`EquipmentCounter`), `genealogy/visitor.py` | Traverse trees / lot graphs and compute results without baking logic into the nodes. |
| **Interpreter** | `workflow/rules.py` | Evaluate the form-validation rules DSL ("weight within ±2 %") as an expression tree. |
| **Memento** | `shared/audit.py` | Each audit entry captures a before/after snapshot; a hash chain makes tampering detectable. |

## Cross-cutting (architectural, not GoF)

- **Repository** (`shared/repository.py`) + **Unit of Work** (`shared/db.session_scope`): modules own their tables; one transaction per operation.
- **Transactional Outbox** (`shared/outbox.py`): events written with the state change, relayed at-least-once (plan decision 4).
