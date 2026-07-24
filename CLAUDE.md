# YTForge — Project Instructions for Claude Code

## What this project is
An AI-powered YouTube Automation Platform: trend discovery → research →
scriptwriting → fact checking → storyboarding → AI image/video/voice/music
generation → automated editing → thumbnails → SEO → approval-gated publishing
→ analytics-driven learning. Multi-channel. Cloud + local AI models.

## Authoritative specs — read these first, follow them strictly
- docs/ARCHITECTURE.md      (full system design, all decisions + rationale)
- docs/PROJECT_STRUCTURE.md (directory layout + coding conventions)

Do not deviate from these documents without flagging the deviation and the
reason. If a spec is ambiguous, ask before improvising.

## Current status
- [x] Phase 1 — Architecture (docs/ARCHITECTURE.md)
- [x] Phase 2 — Folder structure & scaffold (this repo tree)
- [x] Phase 3 — Database: SQLAlchemy 2.0 async models for all aggregates
      (users, channels w/ encrypted OAuth tokens, projects, trends, research,
      scripts, fact_checks, storyboards, scenes, assets, voiceovers,
      voice_profiles, prompt_templates/versions/runs, videos, seo_metadata,
      approvals, analytics_*, jobs, outbox, audit_logs, model_registry,
      api_quota_ledger), Alembic migrations, seed script
- [x] Phase 4 — Backend (domain entities, use cases, FastAPI routers, JWT auth)
- [x] Phase 5 — Frontend (Next.js dashboard, dark mode, SSE pipeline tracker)
- [x] Phase 6 — AI services (provider adapters, ModelRouter, 12 agents,
      prompt template system)
- [x] Phase 7 — Workflow engine (Temporal workflows, approval gates, DLQ)
- [x] Phase 8 — YouTube integration (OAuth, upload w/ synthetic-content
      disclosure, quota ledger, analytics ingestion)
- [x] Phase 9 — Docker (multi-stage images, compose profiles:
      core / observability / local-ai / dev)
- [x] Phase 10 — Deployment (GitHub Actions CI/CD, Grafana/Prometheus/Loki/
      OTel stack, docs: README, developer/deployment/admin guides)

Work phases in order. Update the checklist above as phases complete.

## Hard rules (from the architecture — enforce, don't relitigate)
- Clean Architecture layering: domain → application → infrastructure →
  interfaces. domain/ has ZERO framework or I/O imports. Enforce with
  import-linter.
- Workflow engine is Temporal (not Celery) for the production pipeline.
- All provider integrations go through the ports in
  application/ports/providers/ — never call vendor SDKs from use cases.
- Human approval gates are mandatory before: publishing, scheduling, voice
  cloning, asset deletion. Implemented as Temporal signal waits + an
  approvals table row + audit log entry.
- Events: transactional outbox in Postgres → relay → Redis Streams, with
  events:dlq dead-letter stream. Pipeline sequencing is Temporal-orchestrated;
  events are for side effects/notifications only.
- YouTube uploads must set the synthetic-content disclosure flag when AI
  media is present, and debit the api_quota_ledger (uploads cost 1,600 units).
- Secrets never in YAML/git. Config = YAML (default → env → ENV overrides),
  validated by pydantic-settings at boot.

## Conventions
- Python 3.12, uv-managed, ruff + mypy strict, pytest; async throughout
  application/infrastructure; repository + unit-of-work pattern; UUIDv7 ids;
  UTC timestamps.
- Frontend: Next.js App Router, TypeScript strict, Tailwind, TanStack Query,
  SSE for live updates; dark mode via class strategy.
- Prompt templates: backend/prompts/{agent}/{name}.v{N}.md.j2 with YAML
  front-matter (version, model hints, variables). Never edit a version in
  place — create v{N+1}.
- Every provider adapter records cost + latency via the telemetry layer.
- Tests accompany each phase: unit (pure), integration (testcontainers),
  workflow (Temporal test env w/ time-skipping), e2e (fakeprovider service).

## Commands
- make dev / make test / make lint / make up / make down (wired up starting Phase 9)
- Backend: cd backend && uv sync --extra dev && uv run pytest
- Lint/typecheck: cd backend && uv run ruff check src && uv run mypy src
- DB migrate: cd backend && uv run alembic upgrade head
- DB seed: cd backend && uv run ytforge seed
- DB requires DATABASE_PASSWORD (or YTFORGE__DATABASE__* overrides) in the
  environment — see .env.example and config/*.yaml.
- Frontend: cd frontend && npm install && npm run dev (needs the backend
  running at NEXT_PUBLIC_API_BASE_URL, default http://localhost:8000)
- Frontend lint/typecheck/test: cd frontend && npm run lint && npm run
  typecheck && npm run test
