# deploy/helm/mes — Helm chart (scaffold)

Production deployment target (plan: Kubernetes + Helm). To be filled with:

- `Chart.yaml`, `values.yaml`
- Deployments: `mes-core`, workers (Arq), `edge-gateway` (DaemonSet per plant)
- StatefulSets / subcharts: PostgreSQL + TimescaleDB, NATS JetStream, Redis, Keycloak
- Services, Ingress (TLS), HorizontalPodAutoscaler
- ConfigMaps/Secrets for DB URL, NATS, OIDC (secrets sourced outside the repo)

For local development use `deploy/compose/docker-compose.yml` instead.
