# Deployment Guide

Covers running YTForge outside a dev laptop: Docker Compose profiles, the
observability stack, and the GitHub Actions CI/CD pipeline. For local
development, see the [Developer guide](developer.md).

> **Honesty flag, upfront**: everything in this guide was built and
> reviewed without a Docker daemon or a GitHub remote available in the
> sandbox this project was developed in (see `CLAUDE.md`'s phase notes).
> Every image tag, healthcheck, env var, and workflow step was checked
> against each tool's own docs, but none of it has been exercised
> end-to-end. Treat this the same way you'd treat an unreviewed PR:
> correct to the best of available documentation, verify before relying on
> it in production.

## Docker Compose profiles

`deploy/compose/docker-compose.yml` uses native Compose `profiles:` (not
separate override files) so you compose the stack you need:

| Profile | Services | When |
|---|---|---|
| `core` | postgres, redis, qdrant, minio, temporal, temporal-ui, migrate, api, worker, renderer, outbox-relay, web | Always — the minimum viable stack |
| `observability` | otel-collector, prometheus, grafana, loki, promtail | Whenever you want traces/metrics/logs/dashboards |
| `local-ai` | ollama (GPU reservation) | Running local LLMs instead of cloud providers |
| `dev` | mailpit | Local email capture (auth flows, notifications) |

```bash
cp .env.example .env    # fill in real secrets — never commit .env
make up                                          # core only
make up COMPOSE_PROFILES=core,observability      # + full observability stack
make down                                        # stop, keep volumes
make down-clean                                  # stop, delete volumes
```

`x-backend-env`/`x-backend-image`/`x-depends-on-infra` YAML anchors keep
the `api`/`worker`/`renderer`/`outbox-relay` service blocks DRY — all four
run the same image (or `Dockerfile.renderer` for the FFmpeg-heavy
renderer) with a different `command:` override.

Run the whole `core` stack against fakeprovider (no real AI provider keys
needed) by uncommenting `YTFORGE__MODELS__PROVIDER_SET=fake` in `.env` —
applies to `api`, `worker`, and `renderer` identically.

### TLS / reverse proxy

Per `ARCHITECTURE.md` §13, a TLS-terminating reverse proxy (Caddy) sits in
front of `web` + `api` in production — not included in
`docker-compose.yml` itself, since the TLS cert/domain setup is
environment-specific. Add a `caddy` service (or use a managed
load balancer) that proxies `/api/*` to `api:8000` and everything else to
`web:3000`.

## Observability

### OpenTelemetry

`api`/`worker`/`renderer` export traces, metrics, and trace-correlated logs
via OTLP gRPC when `YTFORGE__OBSERVABILITY__OTEL_EXPORTER_ENDPOINT` is set
(compose sets it to `otel-collector:4317` automatically whenever the
`observability` profile is also running — see `OTEL_EXPORTER_ENDPOINT` in
`.env.example`). Instrumentation is a no-op (using the OTel API's built-in
no-op providers) when the endpoint is unset, so there's no cost to leaving
it off in environments without the `observability` profile.

- Trace propagation across Temporal workflow → activity boundaries goes
  through `TracingInterceptor` (wired on the client and every worker) —
  workflow code itself never creates spans directly (see the
  [Developer guide](developer.md#adding-a-new-temporal-workflow-or-activity)).
- `infrastructure/telemetry/provider_metrics.py`'s `record_provider_call`
  wraps every adapter call in a span and records three metrics:
  `ytforge.provider.call.duration` (histogram), `.cost_usd` (counter),
  `.errors` (counter) — by `provider`/`capability`.
  `infrastructure/telemetry/pipeline_metrics.py` adds
  `ytforge.pipeline.job.failures`, `ytforge.events.dlq.moves`, and
  `ytforge.youtube.quota.remaining`.
- Temporal server's own task-queue depth metrics are exposed via its
  built-in Prometheus endpoint (`PROMETHEUS_ENDPOINT: 0.0.0.0:9091` on the
  `temporal` service), scraped by Prometheus directly — application code
  has no way to compute queue depth itself.

### Prometheus alerts

`deploy/observability/prometheus/alerts.yml` (mounted into the `prometheus`
service, referenced by `prometheus.yml`'s `rule_files`) covers the 4
conditions named in `ARCHITECTURE.md` §9:

| Alert | Condition |
|---|---|
| `YTForgePipelineJobFailure` | Any job transitions to FAILED |
| `YTForgeDlqGrowth` | Sustained (5m+) rate of DLQ moves > 0 |
| `YTForgeQuotaNearExhaustion` | A channel's remaining YouTube quota drops below one upload's cost (1600 units) |
| `YTForgeProviderErrorRateSpike` | >20% of calls to a provider/capability fail over 5m |

The metric names assume the OTel Collector's Prometheus exporter
normalizes dotted OTel instrument names to underscored Prometheus names in
the conventional way (`ytforge.pipeline.job.failures` →
`ytforge_pipeline_job_failures_total`, etc.) — confirm this against a real
`curl otel-collector:8889/metrics` once the stack is actually running, and
correct the alert file if the exporter names anything differently.

### Grafana dashboards

Auto-provisioned from `deploy/observability/grafana/dashboards/` (see
`provisioning/dashboards/dashboards.yml`) on Grafana startup — no manual
import needed:

- **Pipeline Health** — job failure rate, DLQ move rate, provider error
  rate, Temporal task-queue backlog (metric name unverified — see the
  panel description in the dashboard JSON).
- **Provider Costs** — spend by provider/capability, p95 latency, error
  counts.
- **Channel Performance** — reads `analytics_daily_metrics` directly via a
  provisioned **Postgres** Grafana datasource (this data is DB-resident,
  never exported as an OTel metric) plus the one channel-scoped metric
  that IS in the metrics pipeline, quota remaining.
- **Infra** — scrape-target health, OTel Collector self-metrics, Temporal
  reachability. Explicitly does **not** cover container CPU/memory or
  Postgres/Redis/MinIO/Qdrant-internal metrics — no node_exporter/
  postgres_exporter/redis_exporter/cAdvisor is wired up yet; add those
  plus matching `prometheus.yml` scrape jobs before treating this as full
  infra coverage.

Grafana's anonymous viewer access is enabled by default
(`GF_AUTH_ANONYMOUS_ENABLED`) for convenience — disable it before exposing
Grafana outside a trusted network.

## CI/CD (GitHub Actions)

Three workflows under `deploy/github/workflows/` (copied to
`.github/workflows/` so GitHub actually picks them up):

- **`ci.yml`** — on every push/PR to `main`: path-filtered backend/frontend
  lint+typecheck → unit tests → integration tests (testcontainers, needs
  only the runner's own Docker daemon) → db/workflow tests (needs a real
  Postgres service container, since these markers explicitly require a
  reachable Postgres rather than an ephemeral testcontainer).
- **`deploy.yml`** — triggered by `ci.yml` completing successfully on
  `main`. Builds the three deployable images (`api`, `renderer`, `web`)
  multi-arch, scans each with Trivy (fails the job on CRITICAL/HIGH CVEs),
  pushes to GHCR, then a `deploy` job (gated behind a `production` GitHub
  environment, i.e. requires manual approval if you configure required
  reviewers) SSHes into the deploy host and does `docker compose pull && up
  -d`. Needs repo/environment secrets `DEPLOY_HOST`, `DEPLOY_USER`,
  `DEPLOY_SSH_KEY` — none of which exist until you provision a real host.
- **`e2e-nightly.yml`** — scheduled daily (07:00 UTC) + manual dispatch:
  brings up the full `core` compose stack with
  `YTFORGE__MODELS__PROVIDER_SET=fake`, seeds the DB, and runs whatever's
  in `backend/tests/e2e/` and `frontend/tests/e2e/` (both empty scaffolds
  as of Phase 10 — this workflow needs no changes once real specs land).

None of these have been run against a real GitHub remote yet — this repo
had no `.git` at the time Phase 10 was implemented. Before relying on any
of them: push to a real GitHub repo, open a PR, and watch `ci.yml` go
green; then decide whether you want `deploy.yml`'s SSH-based deploy or an
alternative (watchtower polling GHCR, a different target host) before
wiring up the `production` environment's secrets.

## Secrets

`.env` (git-ignored, copy from `.env.example`) holds every secret this
stack reads: `DATABASE_PASSWORD`, `JWT_SECRET`, `ENCRYPTION_MASTER_KEY`
(the KEK for channel OAuth refresh token envelope encryption — losing this
means every stored channel token becomes unrecoverable), Google OAuth
credentials, and one API key var per cloud AI provider. In CI, the
equivalent values are GitHub Actions secrets; in production, they should
come from your host's secret manager rather than a checked-out `.env`
file — the app doesn't care where the environment variables come from, so
this is an infra choice, not a code change.
