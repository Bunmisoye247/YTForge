# YTForge — AI YouTube Automation Platform

## Architecture Specification (Phase 1)

Version 1.0 · Status: Approved baseline for implementation

---

## 1. System Overview

YTForge automates the full YouTube content lifecycle — trend discovery, research,
scriptwriting, fact checking, storyboarding, image/video/voice/music generation,
automated editing, thumbnail creation, SEO metadata, publishing, and analytics-driven
learning — across multiple channels, with mandatory human approval gates before any
irreversible or sensitive action.

The system is a modular monorepo composed of four deployable units plus managed
infrastructure services:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              USERS / OPERATORS                            │
└──────────────────────────────┬────────────────────────────────────────────┘
                               │ HTTPS
                    ┌──────────▼──────────┐
                    │   web (Next.js)     │  Dashboard, approvals, review UI
                    └──────────┬──────────┘
                               │ REST + SSE (JWT)
                    ┌──────────▼──────────┐
                    │   api (FastAPI)     │  Auth, CRUD, approval signals,
                    │                     │  workflow start/query, webhooks
                    └───┬─────┬─────┬─────┘
                        │     │     │
        ┌───────────────▼┐ ┌──▼───────────┐ ┌▼──────────────────────┐
        │ PostgreSQL     │ │ Redis        │ │ Temporal Server        │
        │ (system of     │ │ (cache, rate │ │ (durable workflow      │
        │  record)       │ │  limits,     │ │  orchestration)        │
        │                │ │  streams)    │ │                        │
        └───────▲────────┘ └──▲───────────┘ └───────────▲────────────┘
                │             │                         │ task queues
                │             │             ┌───────────┴────────────┐
                │             │             │  worker (Python)       │
                └─────────────┴─────────────│  Temporal workers +    │
                                            │  agents + providers    │
                                            └─┬────────┬───────┬─────┘
                                              │        │       │
                                   ┌──────────▼─┐ ┌────▼────┐ ┌▼──────────────┐
                                   │ Qdrant     │ │ MinIO   │ │ External APIs │
                                   │ (research  │ │ (media  │ │ LLMs, image/  │
                                   │  vectors)  │ │  assets)│ │ video/voice,  │
                                   └────────────┘ └─────────┘ │ YouTube Data  │
                                                              └───────────────┘
Observability plane: OpenTelemetry SDK in api+worker → OTel Collector →
Prometheus (metrics) / Loki (logs) / Tempo-compatible traces → Grafana.
```

Deployable units: `web` (Next.js), `api` (FastAPI), `worker` (Temporal workers
hosting agents and media processing), `renderer` (FFmpeg-heavy worker pool, same
codebase as `worker` but a separate task queue and container with media tooling
installed, so CPU/GPU-heavy rendering scales independently of I/O-bound agents).

---

## 2. Architectural Style

### 2.1 Clean Architecture layering (backend)

Dependencies point strictly inward. The domain knows nothing about FastAPI,
SQLAlchemy, Temporal, or any vendor SDK.

```
┌──────────────────────────────────────────────────────────────┐
│ interfaces/   HTTP routers, Temporal workflow/activity        │
│               bindings, CLI, event consumers                  │
├──────────────────────────────────────────────────────────────┤
│ infrastructure/  SQLAlchemy repos, Qdrant client, MinIO       │
│                  client, provider adapters (OpenAI, Ollama,   │
│                  ComfyUI, ElevenLabs, Runway, YouTube, …),    │
│                  Redis cache, outbox publisher                │
├──────────────────────────────────────────────────────────────┤
│ application/  Use cases (interactors), ports (abstract        │
│               repositories + provider interfaces), DTOs,      │
│               unit-of-work, domain event dispatch             │
├──────────────────────────────────────────────────────────────┤
│ domain/       Entities, value objects, aggregates, domain     │
│               events, invariants. Pure Python. No I/O.        │
└──────────────────────────────────────────────────────────────┘
```

Rules enforced by import-linter in CI: `domain` imports nothing above it;
`application` imports only `domain`; `infrastructure` implements `application`
ports; `interfaces` wires everything via a dependency-injection container.

### 2.2 Why Temporal (not Celery) for the pipeline

The pipeline is a multi-hour, multi-service, human-in-the-loop process. The
decisive requirements and how each engine meets them:

| Requirement | Temporal | Celery |
|---|---|---|
| Survive worker crash mid-pipeline without losing position | Native (event-sourced workflow history) | Manual state machine + reconciliation |
| Block indefinitely on human approval | `workflow.wait_condition` + signals | Poll loop or chord hacks |
| Per-step retry policy, backoff, non-retryable errors | Declarative `RetryPolicy` per activity | Per-task, but no workflow-level saga |
| Compensation on failure (delete partial renders, refund quota) | Saga pattern in workflow code | Hand-rolled |
| Full execution history for debugging a failed video | Built-in Web UI + history export | Flower shows task states only |
| Versioned workflow code with in-flight migrations | `workflow.patched()` | Not supported |

Celery is retained only for simple recurring jobs where durability is trivial
(analytics polling cron, cache warming) and can be removed entirely if desired —
Temporal cron workflows cover those too. Default configuration uses Temporal for
everything; a `queue.engine` YAML switch exists for the recurring-job class.

### 2.3 Event-driven agent communication

Agents emit and consume **domain events** (`TrendRanked`, `ScriptDrafted`,
`FactCheckFlagged`, `SceneAssetsReady`, `RenderCompleted`, `ApprovalGranted`,
`VideoPublished`, `AnalyticsIngested`, …).

Delivery mechanism — **transactional outbox → Redis Streams**:

1. A use case mutates state and appends events to an `outbox` table in the
   same Postgres transaction (atomicity: no ghost events, no lost events).
2. A relay process reads the outbox and publishes to Redis Streams
   (`events:{aggregate}` topics) with consumer groups per subscriber.
3. Subscribers (notification service, analytics learner, SSE fan-out to the
   dashboard, audit logger) ack per-message; unacked messages are claimed and
   retried; poison messages move to `events:dlq` after N attempts.

Pipeline *sequencing* is NOT event-choreographed — it is orchestrated by
Temporal. Events are for observation, notification, decoupled side effects, and
the learning loop. This "orchestrate the critical path, choreograph the
periphery" split is deliberate: pure choreography makes a 14-stage pipeline
undebuggable.

---

## 3. The Agent System

Each agent is a Python class implementing:

```python
class Agent(Protocol):
    name: str
    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult: ...
```

`AgentContext` provides: the routed LLM (via ModelRouter), tool registry
(web search, Qdrant retrieval, calculator, YouTube data lookup), prompt template
store, budget/token meter, and the event emitter. Agents execute inside Temporal
activities, which supplies heartbeating, timeouts, and retries for free.

| Agent | Consumes | Produces | Key tools |
|---|---|---|---|
| TrendAgent | schedule / manual trigger | `TrendRanked` + trend rows | Google Trends, YT Trending, Reddit, HN, X, RSS, News APIs |
| ResearchAgent | selected trend | research docs + Qdrant chunks, `ResearchCompleted` | web search, fetcher, citation extractor |
| WriterAgent | research context | script draft (structured JSON), `ScriptDrafted` | RAG over Qdrant, style guides |
| FactCheckerAgent | script | verdicts + flags, `FactCheckFlagged`/`Passed` | claim extractor, web search, source cross-check |
| StoryboardAgent | approved script | scene list, `StoryboardReady` | duration estimator, prompt composer |
| ImageAgent | scenes | image assets in MinIO, `SceneImagesReady` | Flux/SDXL/ComfyUI/A1111 adapters |
| VideoAgent | scenes | video clips in MinIO, `SceneClipsReady` | Veo/Runway/Kling/Luma/Hailuo adapters |
| VoiceAgent | script + timing | narration WAV + word timestamps, `NarrationReady` | ElevenLabs/PlayHT/Azure/Kokoro/Piper |
| EditingAgent | all assets | EDL → rendered MP4, `RenderCompleted` | FFmpeg pipeline, silence trimmer, caption burner |
| SEOAgent | script + video | title/desc/tags/chapters/…, `MetadataReady` | keyword tools, competitor titles |
| PublisherAgent | approval | uploaded video, `VideoPublished` | YouTube Data API v3 |
| AnalyticsAgent | schedule | metrics rows + recommendations, `AnalyticsIngested` | YouTube Analytics API |

Learning loop: AnalyticsAgent embeds "what worked" summaries (title patterns,
retention curves vs. script structure, thumbnail CTR) into Qdrant collection
`performance_memory`; WriterAgent, SEOAgent, and Thumbnail generation retrieve
from it, closing requirement #14 (learn from previous performance).

---

## 4. Model & Provider Abstraction

### 4.1 Ports (application layer)

```python
class LLMProvider(Protocol):
    async def complete(self, req: LLMRequest) -> LLMResponse: ...
    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]: ...
    async def embed(self, texts: list[str], model: str) -> list[Vector]: ...
    async def health_check(self) -> None: ...          # raises on failure

class ImageProvider(Protocol):
    async def generate(self, req: ImageRequest) -> list[ImageAsset]: ...
    async def health_check(self) -> None: ...

class VideoProvider(Protocol):
    async def generate(self, req: VideoRequest) -> VideoJob: ...      # async jobs
    async def poll(self, job: VideoJob) -> VideoJobStatus: ...
    async def health_check(self) -> None: ...

class TTSProvider(Protocol):
    async def synthesize(self, req: TTSRequest) -> AudioAsset: ...    # + timestamps
    async def clone_voice(self, req: VoiceCloneRequest) -> VoiceProfile: ...  # approval-gated
    async def health_check(self) -> None: ...

class MusicProvider(Protocol):
    async def generate(self, req: MusicRequest) -> AudioAsset: ...
    async def health_check(self) -> None: ...
```

Every adapter implements `health_check()` as a cheap, short-timeout ping
(model-list endpoint where one is documented, a bare-root connectivity
probe otherwise) — `ProviderHttpClient.ping()` raises the same
`ProviderError` hierarchy the real calls use, so a health check and a real
call fail identically. `VideoProductionWorkflow`'s pre-flight step (§5.1)
is the only current caller: it dry-runs each route's primary/fallback
chain against `health_check()` instead of a real request.

### 4.2 Adapters (infrastructure layer)

LLM: `openai`, `anthropic`, `gemini`, `groq` (free-tier, OpenAI-compatible),
`ollama` (Qwen/Llama/DeepSeek/Mistral), `lmstudio` (OpenAI-compatible).
Image: `flux_api`, `pollinations` (free, keyless), `sdxl_diffusers`,
`comfyui`, `a1111`. Video: `veo`, `runway`, `kling`, `luma`, `hailuo`. TTS:
`elevenlabs`, `playht`, `azure_tts`, `kokoro` (local, CPU-friendly),
`piper`. Music: `suno`, `udio`, `mubert`.

Which adapter is *primary* per route is a deployment choice, not an
architectural one — `config/default.yaml` picks free/local-first defaults
(Pollinations for images, Kokoro for voice, small Ollama models for
routes that don't need frontier quality) to keep a GPU-constrained box
running without paid keys; swap the `primary`/`fallback` order for a box
with more VRAM or a paid-API budget instead.

### 4.3 ModelRouter

YAML-driven routing with capability tags, fallback chains, and cost/latency
budgets:

```yaml
models:
  routes:
    script_writing:   {primary: anthropic/claude-sonnet-4-6, fallback: [openai/gpt-4.1, ollama/qwen2.5:72b]}
    fact_checking:    {primary: openai/gpt-4.1, fallback: [anthropic/claude-sonnet-4-6]}
    seo:              {primary: ollama/llama3.3:70b, fallback: [gemini/gemini-2.0-flash]}
    embeddings:       {primary: openai/text-embedding-3-large, fallback: [ollama/nomic-embed-text]}
  discovery:
    ollama:    {base_url: http://ollama:11434, auto_detect: true}   # GET /api/tags
    lmstudio:  {base_url: http://lmstudio:1234, auto_detect: true}  # GET /v1/models
    comfyui:   {base_url: http://comfyui:8188, auto_detect: true}   # object_info scan
```

Auto-detection runs at worker boot and on a schedule; discovered models register
in a `model_registry` table and surface in the dashboard Settings page.

---

## 5. Workflow Engine Design

### 5.1 Main pipeline (Temporal workflow `VideoProductionWorkflow`)

Stages as activities, each with tailored retry policy and timeouts:

```
Preflight → Research → ScriptWrite → FactCheck ──(flags?)──► HumanReview
      │                                        │pass
      ▼                                        ▼
  (standalone cron)                       Storyboard
                                               ▼
                              ┌────────────────┼────────────────┐
                              ▼                ▼                ▼
                        ImageGen(scenes)  VideoGen(scenes)  VoiceGen     ← parallel fan-out
                              └────────────────┼────────────────┘
                                               ▼
                                            Editing (renderer queue)
                                               ▼
                                   Thumbnail  +  SEO (parallel)
                                               ▼
                                     ══ APPROVAL GATE ══  (signal wait, days-long OK)
                                               ▼
                                            Upload
                                               ▼
                                   Schedule / Publish (child workflow, timer)
                                               ▼
                                  Analytics collection (cron child, 30 days)
```

Preflight runs first, before Research — it resolves every route
`VideoProductionWorkflow` will need (script_writing, image_generation,
video_generation, voice_synthesis, …), health-checks each route's
primary/fallback chain concurrently, and fails the run immediately with a
per-route error if a route has *no* healthy candidate at all. This is the
same failure a misconfigured or offline provider would otherwise only
surface as `AllProvidersExhaustedError` minutes into a real run, at the
expensive media-generation fan-out — pre-flight just runs the same
resolution against `health_check()` instead of a real request, in
parallel, before any billable/GPU work starts.

Design details:
- **Fan-out/fan-in per scene**: image and clip generation run as parallel
  activities bounded by a semaphore (provider rate limits), results merged
  before editing.
- **Long-poll external render jobs** (Runway, Veo, Suno) via activity
  heartbeats; cancellation propagates to provider cancel endpoints.
- **Saga compensation**: on terminal failure after asset creation, a
  compensation branch marks assets orphaned (soft delete — hard deletion is
  itself approval-gated).
- **Determinism**: all I/O in activities; workflow code is pure orchestration;
  versioning via `workflow.patched()` for in-flight upgrades.
- **Budget guard**: workflow tracks accumulated provider spend; exceeding the
  project budget pauses at a review gate instead of burning money.

### 5.2 Approval gates

`ApprovalGate(kind, payload)` is a reusable sub-pattern: persist an
`approvals` row (pending), emit `ApprovalRequested` (→ dashboard SSE +
email/Slack notification), then `await workflow.wait_condition(...)` for a
signal delivered by `POST /approvals/{id}/decision`. Gated actions: **publish,
schedule, voice cloning, asset deletion**. Every decision records who, when,
and an optional note — a full audit trail.

### 5.3 Error handling

Per-activity `RetryPolicy` (exponential backoff, max attempts, non-retryable
error types like `QuotaExhausted`, `ContentPolicyViolation`). Exhausted retries
raise to the workflow, which routes to a `FailureHandler` activity: persist
failure, emit `PipelineFailed` (→ notifications), optionally park the workflow
in a "needs operator" state resumable by signal. Event-bus consumers use Redis
Streams pending-entry claiming with `events:dlq` as the dead-letter stream and
an operator UI for inspect/replay/discard. Recovery: `temporal workflow reset`
restores any pipeline to a prior decision point.

---

## 6. Data Architecture

### 6.1 PostgreSQL — system of record

Aggregates (full DDL in Phase 3): `users`, `channels` (OAuth tokens encrypted
via envelope encryption, brand kit, defaults), `projects`, `trends`,
`research_documents`, `scripts` (versioned, structured JSON sections),
`fact_checks`, `storyboards` + `scenes`, `assets` (typed: image/clip/audio/
music/thumbnail/render; MinIO object key + checksums + provenance), `voiceovers`
(+ `voice_profiles` with consent record for cloning), `prompt_templates` +
`prompt_versions` + `prompt_runs` (testing & history), `videos` (final entity;
YouTube video id, disclosure flags), `seo_metadata`, `approvals`, `analytics_*`
(daily metrics, retention curves, traffic sources), `jobs` (Temporal run
mirror for dashboard queries), `outbox`, `audit_logs`, `model_registry`,
`api_quota_ledger` (YouTube unit budget tracking).

### 6.2 Qdrant — semantic memory

Collections: `research` (chunked research docs; payload: project, source URL,
published_at, citation), `performance_memory` (post-hoc analyses of published
videos), `script_library` (past scripts for style retrieval), `trend_history`
(deduplication of recurring topics). Hybrid search (dense + sparse) for
research retrieval.

### 6.3 MinIO — media object storage

Buckets: `raw-assets` (generated images/clips/audio), `renders` (intermediates
+ finals), `thumbnails`, `voices` (cloning samples, restricted policy),
`exports`. Keys: `{channel_id}/{project_id}/{asset_type}/{asset_id}.{ext}`.
Lifecycle rules expire intermediates after N days; finals retained. All
dashboard media access via presigned URLs — the API never proxies bytes.

### 6.4 Redis

DB-separated roles: cache (API responses, trend snapshots, model registry),
rate limiting (per-provider token buckets), Redis Streams event bus, SSE
fan-out pub/sub, distributed locks (e.g., one analytics poll per channel).

---

## 7. API & Frontend Architecture

### 7.1 API (FastAPI)

Versioned REST under `/api/v1`: `auth` (register/login/refresh; Google OAuth
for YouTube channel linking), `channels`, `projects`, `trends`, `research`,
`scripts`, `storyboards`, `assets`, `videos`, `pipelines` (start/status/cancel/
signal), `approvals`, `prompts`, `analytics`, `models`, `settings`, `events`
(SSE stream), `webhooks` (provider callbacks, HMAC-verified). JWT access
(15 min) + rotating refresh tokens (httpOnly cookie); RBAC roles
owner/admin/editor/viewer scoped per channel. Rate limiting, request-id
propagation, OTel middleware, RFC 7807 problem+json errors.

### 7.2 Frontend (Next.js App Router, TypeScript, Tailwind)

Server components for data-heavy pages, client components for interactive
review tools. TanStack Query for server state; SSE hook for live pipeline
progress. Pages: Overview (KPIs, live pipelines, pending approvals), Projects
(kanban by stage), Channels, Ideas (trend explorer with score breakdown),
Scripts (versioned editor + fact-check flag overlay), Storyboards (scene
timeline), Images / Videos (asset galleries, regenerate-with-edited-prompt),
Uploads (schedule calendar), Analytics (retention curves, CTR, revenue),
Settings (models, prompts, YAML config editor, integrations). Dark mode via
class strategy + system preference, persisted.

---

## 8. Security

Secrets via env/secret files, never in YAML committed to git (YAML references
`${ENV_VAR}`). Channel OAuth refresh tokens encrypted with per-record data keys
(envelope encryption, master key external). Voice cloning requires recorded
consent artifact + approval before the provider call. Webhook HMAC
verification. Principle-of-least-privilege MinIO policies. Audit log on every
approval, publish, deletion, and settings change. Dependency scanning + image
scanning in CI. YouTube compliance: synthetic-content disclosure flag set on
upload when AI media present; API quota ledger prevents silent quota
exhaustion; per-channel upload pacing to avoid spam signals.

---

## 9. Observability

OTel SDK in api/worker/renderer → OTel Collector. Traces span the entire
pipeline (workflow → activity → provider call) with `project_id`,
`channel_id`, `workflow_id` attributes. Prometheus metrics: pipeline stage
durations, provider latency/error/cost counters, queue depths, render times,
YouTube quota remaining. Loki structured JSON logs correlated by trace id.
Grafana dashboards: Pipeline Health, Provider Costs, Channel Performance,
Infra. Alerting: pipeline failure, DLQ growth, quota near-exhaustion, provider
error-rate spikes.

---

## 10. Testing Strategy

Unit (domain + application, no I/O, fast); integration (repos against real
Postgres/Qdrant/MinIO/Redis via testcontainers; provider adapters against
recorded cassettes); workflow tests (Temporal test framework with time
skipping — approval gates and long timers testable in milliseconds); E2E
(docker-compose stack + Playwright driving dashboard through a full pipeline
with all providers mocked by a `fakeprovider` service); performance (Locust on
API, render throughput benchmarks). Coverage gates in CI.

---

## 11. Configuration Model

Single `config/` tree of YAML, merged in order: `default.yaml` →
`{env}.yaml` → env-var overrides (`YTFORGE__SECTION__KEY`). Sections: `app`,
`database`, `redis`, `qdrant`, `minio`, `temporal`, `models` (routing +
discovery), `providers` (per-provider settings, rate limits, cost tables),
`pipeline` (stage toggles, parallelism, budgets), `approvals`, `notifications`
(email/Slack/webhook), `youtube` (quota budget, defaults), `observability`.
Pydantic-settings validates the merged config at boot; invalid config fails
fast with a precise error.

---

## 12. CI/CD (GitHub Actions)

Pipelines: lint+typecheck (ruff, mypy, eslint, tsc, import-linter layer check)
→ unit tests → integration tests (service containers) → build multi-arch
Docker images → scan → push to GHCR → deploy job (compose pull+up via SSH or
watchtower). Frontend and backend pipelines path-filtered; a nightly E2E run
executes the full mocked pipeline.

---

## 13. Deployment Topology (Docker Compose)

Profiles: `core` (postgres, redis, qdrant, minio, temporal, temporal-ui, api,
worker, renderer, web, outbox-relay), `observability` (otel-collector,
prometheus, grafana, loki, promtail), `local-ai` (ollama, comfyui — GPU
reservation), `dev` (mailpit, fakeprovider). Healthchecks + `depends_on:
condition: service_healthy` ordering; named volumes for all state; single
`.env` for secrets; Caddy as TLS-terminating reverse proxy in front of web+api.

---

## 14. Phase Map (implementation order)

P1 Architecture (this document) · P2 Folder structure + scaffold · P3 Database
(SQLAlchemy models, Alembic migrations, seed) · P4 Backend (domain, use cases,
API, auth) · P5 Frontend (dashboard) · P6 AI services (providers, agents,
prompt system) · P7 Workflow engine (Temporal workflows/activities, approval
gates, DLQ) · P8 YouTube integration (OAuth, upload, analytics) · P9 Docker
(images, compose profiles) · P10 Deployment (CI/CD, observability stack, docs).
