# YTForge — AI YouTube Automation Platform

Enterprise platform automating the full YouTube content lifecycle: trend
discovery → research → scriptwriting → fact checking → storyboarding → AI
image/video/voice/music generation → automated editing → thumbnails → SEO →
approval-gated publishing → analytics-driven learning. Multi-channel, cloud
and local AI models, human approval gates for all sensitive actions.

- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Structure & conventions: [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- Guides: [Developer](docs/guides/developer.md) ·
  [Deployment](docs/guides/deployment.md) · [Admin](docs/guides/admin.md)
- Stack: Next.js · FastAPI · Temporal · PostgreSQL · Redis · Qdrant · MinIO ·
  Docker Compose · Prometheus/Grafana/Loki · OpenTelemetry

## Status

- [x] P1 Architecture · [x] P2 Folder structure & scaffold
- [x] P3 Database (SQLAlchemy models, Alembic migrations, seed)
- [x] P4 Backend (domain, use cases, API, auth)
- [x] P5 Frontend (Next.js dashboard)
- [x] P6 AI services (providers, ModelRouter, 12 agents, prompt system)
- [x] P7 Workflow engine (Temporal workflows/activities, approval gates, DLQ)
- [x] P8 YouTube integration (OAuth, upload, quota ledger, analytics)
- [x] P9 Docker (multi-stage images, compose profiles)
- [x] P10 Deployment (CI/CD, observability stack, docs)

## Quickstart (local, no Docker)

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), Node 22, and a local
Postgres/Redis/Qdrant/MinIO/Temporal — or use the Docker path below instead.

```bash
cp .env.example .env   # fill in DATABASE_PASSWORD, JWT_SECRET at minimum
cd backend && uv sync --extra dev
uv run alembic upgrade head
uv run ytforge seed
uv run ytforge serve   # http://localhost:8000

# in another shell
cd frontend && npm install && npm run dev   # http://localhost:3000
```

Run everything against deterministic fake providers (no API keys, no local
model servers) by setting `YTFORGE__MODELS__PROVIDER_SET=fake` before
`ytforge serve` / `run-worker` / `run-renderer`.

## Quickstart (Docker Compose)

```bash
cp .env.example .env   # fill in DATABASE_PASSWORD, JWT_SECRET at minimum
make up                                        # core profile only
make up COMPOSE_PROFILES=core,observability    # + Prometheus/Grafana/Loki
make up COMPOSE_PROFILES=core,dev              # + mailpit
make down            # stop (keep volumes)
make down-clean       # stop and delete volumes
```

See the [Deployment guide](docs/guides/deployment.md) for profile details,
the [Developer guide](docs/guides/developer.md) for day-to-day workflow, and
the [Admin guide](docs/guides/admin.md) for operating a running instance
(approvals, quota, incident response).

## Commands

| Command | What it does |
|---|---|
| `make dev` | Backend + frontend dev servers, no Docker |
| `make test` | Backend pytest (unit) + frontend vitest |
| `make lint` | ruff + mypy + import-linter, eslint + tsc |
| `make up` / `make down` | Docker Compose up/down (`COMPOSE_PROFILES` env var selects profiles) |
| `cd backend && uv run alembic upgrade head` | Apply DB migrations |
| `cd backend && uv run ytforge seed` | Seed dev data |
| `cd backend && uv run ytforge sync-prompts` | Load `backend/prompts/**` into `prompt_templates` |
| `cd backend && uv run ytforge run-agent <name> --project-id=<id>` | Manually invoke one agent outside Temporal |

## Repository layout

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for the full
directory map and coding conventions (Clean Architecture layering, UUIDv7
ids, prompt template versioning, testing pyramid). In short:

```
backend/    FastAPI + Temporal app: domain -> application -> infrastructure -> interfaces
frontend/   Next.js App Router dashboard
config/     YAML config (default -> per-env -> ${ENV_VAR} overrides)
deploy/     Docker images, compose profiles, observability stack, CI/CD workflows
docs/       Architecture, structure, and this repo's guides/diagrams/api docs
```
