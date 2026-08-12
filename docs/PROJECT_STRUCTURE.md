# YTForge — Project Structure (Phase 2)

Monorepo rationale: four deployable units share domain types, prompt templates,
and config schemas; cross-cutting changes stay atomic. Backend top-level
packages ARE the Clean Architecture layers, so illegal dependencies are
visually obvious and enforced by import-linter in CI.

```
ytforge/
├── backend/
│   ├── pyproject.toml                  # uv/poetry; deps, ruff, mypy, pytest config
│   ├── alembic.ini
│   ├── Dockerfile                      # api + worker (multi-stage)
│   ├── Dockerfile.renderer             # + ffmpeg, fonts, media libs
│   ├── prompts/                        # versioned prompt templates (Jinja2 + YAML front-matter)
│   │   ├── trend/  research/  writer/  fact_checker/  storyboard/
│   │   ├── image/  video_gen/  voice/  seo/  analytics/
│   │   └── (each: {name}.v{N}.md.j2 — version in filename, metadata header)
│   ├── src/ytforge/
│   │   ├── domain/                     # LAYER 1 — pure business logic, zero I/O
│   │   │   ├── entities/               # User, Channel, Project, Trend, Script,
│   │   │   │                           # Scene, Asset, Voiceover, Video, Approval…
│   │   │   ├── value_objects/          # Duration, AspectRatio, ScriptSection,
│   │   │   │                           # TrendScore, Money, ObjectKey, VoiceStyle…
│   │   │   ├── events/                 # domain events (TrendRanked, ScriptDrafted…)
│   │   │   └── services/               # pure domain services (scoring, timing math)
│   │   ├── application/                # LAYER 2 — use cases + ports
│   │   │   ├── ports/
│   │   │   │   ├── repositories/       # abstract repos (ChannelRepo, ScriptRepo…)
│   │   │   │   └── providers/          # LLMProvider, ImageProvider, VideoProvider,
│   │   │   │                           # TTSProvider, MusicProvider, SearchProvider,
│   │   │   │                           # ObjectStorage, VectorStore, EventPublisher,
│   │   │   │                           # YouTubeGateway, Notifier, UnitOfWork
│   │   │   ├── use_cases/              # one folder per bounded capability
│   │   │   │   ├── trends/ research/ scripts/ fact_check/ storyboard/
│   │   │   │   ├── assets/ voice/ editing/ thumbnails/ seo/
│   │   │   │   ├── publishing/ analytics/ approvals/ prompts/
│   │   │   │   └── channels/ projects/ auth/
│   │   │   ├── dto/                    # request/response models between layers
│   │   │   └── common/                 # Result type, errors, pagination, budget meter
│   │   ├── infrastructure/             # LAYER 3 — adapters
│   │   │   ├── db/
│   │   │   │   ├── models/             # SQLAlchemy ORM models
│   │   │   │   ├── repositories/       # port implementations
│   │   │   │   └── migrations/         # Alembic env + versions/
│   │   │   ├── vector/                 # Qdrant adapter (collections, hybrid search)
│   │   │   ├── storage/                # MinIO adapter, presigned URLs, lifecycle
│   │   │   ├── cache/                  # Redis cache, rate limiters, locks
│   │   │   ├── events/                 # outbox writer, relay, Redis Streams pub/sub, DLQ
│   │   │   ├── providers/
│   │   │   │   ├── llm/                # openai, anthropic, gemini, groq, ollama, lmstudio, router
│   │   │   │   ├── image/              # flux, pollinations, sdxl, comfyui, a1111
│   │   │   │   ├── video/              # veo, runway, kling, luma, hailuo
│   │   │   │   ├── tts/                # elevenlabs, playht, azure, kokoro, piper
│   │   │   │   └── music/              # suno, udio, mubert
│   │   │   │   # every adapter implements health_check() (its Protocol's
│   │   │   │   # method) — see interfaces/activities/pipeline_activities.py's
│   │   │   │   # preflight_check activity, the only current caller
│   │   │   ├── external/
│   │   │   │   ├── youtube/            # Data API v3 + Analytics API + quota ledger
│   │   │   │   └── trends_sources/     # gtrends, reddit, hn, x, rss, newsapi
│   │   │   ├── security/               # JWT, password hashing, envelope encryption
│   │   │   ├── config/                 # YAML loader + pydantic-settings schemas
│   │   │   └── telemetry/              # OTel setup, metrics, structured logging
│   │   └── interfaces/                 # LAYER 4 — delivery mechanisms
│   │       ├── api/
│   │       │   ├── main.py             # FastAPI app factory
│   │       │   ├── routers/            # auth, channels, projects, trends, scripts,
│   │       │   │                       # storyboards, assets, videos, pipelines,
│   │       │   │                       # approvals, prompts, analytics, models,
│   │       │   │                       # settings, events(SSE), webhooks
│   │       │   ├── middleware/         # auth, rate limit, request-id, OTel, errors
│   │       │   ├── schemas/            # Pydantic request/response models
│   │       │   └── deps/               # DI wiring (container → route deps)
│   │       ├── workflows/              # Temporal workflows (VideoProduction,
│   │       │                           # ApprovalGate, ScheduledPublish,
│   │       │                           # AnalyticsCron, TrendDiscoveryCron)
│   │       ├── activities/             # Temporal activities (thin: call use cases)
│   │       ├── agents/                 # the 12 agents + base Agent, tool registry
│   │       ├── consumers/              # Redis Streams subscribers (notify, SSE, audit)
│   │       └── cli/                    # ytforge CLI: run-worker, run-renderer,
│   │                                   # migrate, seed, detect-models, replay-dlq
│   └── tests/
│       ├── unit/{domain,application}/  # pure, fast
│       ├── integration/                # testcontainers: pg, redis, qdrant, minio
│       ├── workflows/                  # Temporal test env, time-skipping
│       ├── e2e/                        # full stack, fakeprovider
│       ├── performance/                # locust files, render benchmarks
│       └── fixtures/                   # factories, cassettes, sample media
├── frontend/
│   ├── package.json  next.config.ts  tailwind.config.ts  tsconfig.json  Dockerfile
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/{login,register}/
│   │   │   └── (dashboard)/{overview,projects,channels,ideas,scripts,
│   │   │        storyboards,images,videos,uploads,analytics,settings}/
│   │   ├── components/
│   │   │   ├── ui/                     # primitives (button, dialog, table…)
│   │   │   ├── layout/                 # shell, sidebar, theme toggle (dark mode)
│   │   │   ├── pipeline/               # live stage tracker (SSE)
│   │   │   ├── approvals/              # approval inbox + decision modals
│   │   │   ├── charts/                 # retention, CTR, revenue
│   │   │   └── editors/                # script editor, scene timeline, prompt editor
│   │   ├── lib/{api,hooks,stores,utils}/   # typed client, SSE hook, TanStack Query
│   │   ├── styles/  types/
│   └── tests/{unit,e2e}/               # vitest, playwright
├── config/                             # YAML config tree (merged default→env→ENV)
│   ├── default.yaml  development.yaml  production.yaml
│   └── (sections: app, database, redis, qdrant, minio, temporal, models,
│        providers, pipeline, approvals, notifications, youtube, observability)
├── deploy/
│   ├── compose/                        # docker-compose.yml + profile overrides
│   │   └── (core / observability / local-ai / dev profiles)
│   ├── docker/                         # shared build assets, entrypoints
│   ├── caddy/                          # reverse proxy + TLS
│   ├── observability/{grafana,prometheus,loki,otel}/
│   └── github/workflows/               # ci.yml, e2e-nightly.yml, deploy.yml
│                                       # (symlinked/copied to .github/workflows)
├── scripts/                            # dev bootstrap, db seed, model detect
├── docs/
│   ├── ARCHITECTURE.md  PROJECT_STRUCTURE.md
│   ├── diagrams/  api/  guides/        # developer, deployment, admin guides
├── Makefile                            # make dev / test / lint / e2e / up / down
├── .env.example
└── README.md
```

Conventions locked in for all later phases: Python 3.12, uv-managed; ruff +
mypy strict; async everywhere in application/infrastructure; repository +
unit-of-work pattern; all IDs UUIDv7; all timestamps UTC; prompt files carry
version in the filename and metadata in YAML front-matter; every provider
adapter records cost + latency to the telemetry layer.
