# Developer Guide

Day-to-day workflow for working on YTForge. For the system design and the
"why" behind these rules, read [docs/ARCHITECTURE.md](../ARCHITECTURE.md)
first; for directory layout and naming conventions, read
[docs/PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md). This guide doesn't
repeat either — it's the missing "how do I actually work in this repo"
piece.

## Setup

```bash
cp .env.example .env
# minimum to boot: DATABASE_PASSWORD, JWT_SECRET, ENCRYPTION_MASTER_KEY
# (openssl rand -base64 32)
```

You need a reachable Postgres, Redis, Qdrant, MinIO, and Temporal server.
Either run them via `make up` (Docker) or point `YTFORGE__*` env overrides
at your own local instances — see `.env.example` for every override name.

```bash
cd backend && uv sync --extra dev
uv run alembic upgrade head
uv run ytforge seed
uv run ytforge sync-prompts   # loads backend/prompts/** into prompt_templates
uv run ytforge serve
```

```bash
cd frontend && npm install && npm run dev
```

## Running things without real AI provider keys

Set `YTFORGE__MODELS__PROVIDER_SET=fake` (env or `.env`). Every LLM/image/
video/TTS/music port resolves to `infrastructure/providers/fakeprovider/`
instead — deterministic canned output, no network calls, no cost. This is
what CI's integration tests and the nightly e2e run use; use it locally too
whenever you're working on pipeline/orchestration logic rather than a
specific provider adapter.

## Testing

Four pytest markers, matching how much infrastructure each tier needs
(`backend/pyproject.toml`'s `[tool.pytest.ini_options]`):

| Command | Needs | What it covers |
|---|---|---|
| `uv run pytest tests/unit tests/performance -m "not integration and not workflow and not db"` | Nothing | Pure unit tests — domain, application use cases (via `FakeUnitOfWork`), agents (via fakeprovider), adapters (via `respx`-mocked httpx) |
| `uv run pytest tests/integration -m integration` | Docker daemon (testcontainers spins its own containers) | Full-stack API tests against a real ephemeral Postgres |
| `uv run pytest tests/db -m db` | A reachable local Postgres (`DATABASE_PASSWORD` set, migrations applied) | Repository-layer tests against real SQL |
| `uv run pytest tests/workflows -m workflow` | A reachable local Postgres + outbound network (downloads Temporal's embedded time-skipping test server on first run) | Temporal workflow determinism/replay tests |

`make test` runs the no-infra tier plus the frontend's `vitest` suite —
that's also what CI's `backend-unit-tests`/`frontend-unit-tests` jobs run
on every push. The other three tiers each get their own CI job with the
matching service container (see `.github/workflows/ci.yml`).

`backend/tests/e2e/` and `frontend/tests/e2e/` (Playwright) are currently
empty scaffolds — `deploy/github/workflows/e2e-nightly.yml` already brings
up the full compose stack with fakeprovider and runs whatever lands there,
so adding real e2e specs needs no workflow changes.

## Adding a new provider adapter

1. Implement the matching `Protocol` from `application/ports/providers/`
   in `infrastructure/providers/{category}/{name}.py`. Prefer
   `infrastructure.providers.http_base.ProviderHttpClient` over a bare
   `httpx.AsyncClient` — it wraps HTTP status codes *and* raw connection
   failures into the shared `ProviderError` hierarchy, which is what lets
   `ConfigDrivenModelRouter`'s fallback loop correctly skip an unreachable
   provider instead of crashing the whole route (a bare `httpx.AsyncClient`
   only gets you the status-code half of that). Wrap the call in
   `infrastructure.telemetry.provider_metrics.record_provider_call` (this
   is what gives you cost/latency/error metrics and a trace span for free
   — see the [Deployment guide](deployment.md#observability) for where
   those end up). Every port also requires a `health_check(self) -> None`
   method: a cheap, short-timeout call (`ProviderHttpClient.ping(path)` if
   you're using it) that raises on failure and returns `None` on success —
   this is what `VideoProductionWorkflow`'s pre-flight step calls before
   any expensive pipeline work starts (see
   `interfaces/activities/pipeline_activities.py`'s `_evaluate_preflight`).
2. Register it in `infrastructure/providers/registry.py`'s
   `build_real_registries` (and `build_fake_registries` if you want the
   fake provider set to include its key too), add its `ProviderSettings`
   field to `ProvidersSettings` in `infrastructure/config/settings.py`, and
   add its config block to `config/default.yaml`'s `providers:` section +
   a key var line in `.env.example`.
3. Add a `respx`-mocked unit test under
   `tests/unit/infrastructure/providers/`, including a case for
   `health_check()` (success and failure).
4. Never call the adapter directly from an agent or use case — agents only
   go through `ModelRouter`.

## Adding a new agent

Agents live in `interfaces/agents/`, one file each, following: render a
prompt template → route through `ModelRouter` → parse output → call an
**existing** application-layer use case to persist it → return
`AgentResult`. They do not open a parallel persistence path; if the use
case you need doesn't exist yet, add it to `application/use_cases/` first,
the same way an API router would.

Prompt templates live at `backend/prompts/{agent}/{name}.v{N}.md.j2` with
YAML front-matter (`version`, `model_hints`, `variables`). **Never edit a
version in place** — copy to `v{N+1}.md.j2`, bump the front-matter version,
and run `uv run ytforge sync-prompts` to load it into `prompt_templates`/
`prompt_versions`.

## Adding a new Temporal workflow or activity

Read the note at the top of `interfaces/workflows/video_production.py`
before touching this layer — it's the one place in the codebase with a
hard framework constraint that isn't obvious from the type signatures:

- Workflow files (`interfaces/workflows/*.py`) must **never** import from
  `interfaces.activities` — that package transitively pulls in sqlalchemy/
  httpx and does module-level filesystem work, both of which trip
  Temporal's sandboxed-workflow-code restrictions. Activity input/output
  DTOs live in the sibling `interfaces/activity_dto.py` instead.
- Activities are referenced by **string name**
  (`workflow.execute_activity("activity_name", ..., result_type=...)`),
  never by importing the activity function into workflow code.
- Workflow `run()` bodies must never create OTel spans/metrics directly —
  that's what `TracingInterceptor` (wired on the client and every worker)
  is for. Record any hand-rolled metric (job failures, DLQ moves, quota
  remaining) from the **activity**, not the workflow.

## Clean Architecture layering

`domain -> application -> infrastructure -> interfaces`, enforced by
`import-linter` (`uv run lint-imports`, also a CI job). `domain/` has zero
framework or I/O imports — no SQLAlchemy, no httpx, no FastAPI. If you find
yourself wanting to import something infrastructure-flavored into
`domain/` or `application/`, the fix is almost always a new port
(`Protocol`) in `application/ports/`, implemented in `infrastructure/`.

## Config

`config/default.yaml` → `config/{env}.yaml` → `${ENV_VAR}` interpolation →
direct `YTFORGE__SECTION__KEY` env overrides (highest precedence),
validated by `pydantic-settings` at boot (`infrastructure/config/
settings.py`). Never put secrets in the YAML files — they're checked in;
`${VAR}` placeholders resolve from `.env` (local) or real environment
variables (deployed).

## Database migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "add foo column"
uv run alembic upgrade head
```

Review the autogenerated migration — SQLAlchemy 2.0's autogenerate is good
but not perfect on things like server-side defaults or renamed columns.
