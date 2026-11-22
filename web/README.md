# web — MES front-end (scaffold)

React + TypeScript + Vite front-end for the three personas in the architecture
plan. Not yet implemented; this placeholder reserves the structure.

```
web/
  operator/      Operator terminal (tablet/kiosk): login at station, pick order,
                 start/pause/complete operations, scan lots, fill step forms.
  supervisor/    Dispatch lists, order status, andon board, OEE dashboards.
  admin/         Equipment-tree + route modeling, reason-code trees, master data.
  shared/        API client (TanStack Query), auth (Keycloak OIDC), UI (shadcn),
                 charts (ECharts), WebSocket hooks for real-time status.
```

Backend contract: the REST + WebSocket API served by `mes_core` (OpenAPI at
`/docs`). Real-time updates (order status, machine state, andon) arrive over
WebSocket; all mutating operator actions send a client-generated `X-Request-Id`
so retries are idempotent (see `mes_core.shared.commands`).
