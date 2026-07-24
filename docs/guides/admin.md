# Admin Guide

Operating a running YTForge instance day-to-day: approvals, channels,
quota, budgets, and incident response. For installing/upgrading the
stack, see the [Deployment guide](deployment.md); for how the pipeline
works internally, see [docs/ARCHITECTURE.md](../ARCHITECTURE.md) §5.

## Approval gates

Four actions are hard-gated behind human approval (`CLAUDE.md`'s rule,
`domain/enums.py`'s `ApprovalKind`): **publishing**, **scheduling**,
**voice cloning**, and **asset deletion** — plus a fifth,
non-mandatory-but-wired-the-same-way gate for a fact-check flagged as
needing human review before storyboarding proceeds.

- List pending approvals: `GET /approvals?status_filter=pending` (the
  Phase-5 dashboard's Approvals page is the same call).
- Approve/reject: `POST /approvals/{approval_id}/decision` with
  `{"status": "approved" | "rejected", "note": "..."}`. If the approval is
  tied to a running Temporal workflow (`approval.workflow_id` set), the API
  signals that workflow directly — the pipeline resumes (or the saga
  compensates, for a rejection) within seconds, no polling involved.
- Every decision is written to `audit_logs` (`GET /audit-logs`) — who
  decided, when, and the note, alongside the approval row itself.

If a workflow's approval wait seems stuck: check the Temporal UI
(`:8080` when the `core` profile is up) for the workflow's current state
before assuming the API/signal path is broken — a workflow that failed
upstream of the approval-request activity will never have created the
approval row you're looking for in the first place.

## Channels & YouTube quota

- Link a channel: the OAuth flow issues `channels.oauth_refresh_token`,
  stored envelope-encrypted (AES-GCM, KEK = `ENCRYPTION_MASTER_KEY`) —
  rotating that key requires re-linking every channel, so back it up
  outside the Postgres backup itself (see Backup/restore below).
- Every YouTube upload debits `api_quota_ledger` (1,600 units per upload,
  `CLAUDE.md`'s hard rule) against a per-channel daily budget
  (`config/default.yaml`'s `youtube.daily_quota_budget`, override via
  `YTFORGE__YOUTUBE__DAILY_QUOTA_BUDGET`; defaults to 10,000, matching
  YouTube's own default per-project daily allocation). `PublisherAgent`
  checks remaining budget before every upload and refuses rather than
  partially uploading when it would exceed the budget.
- Watch `ytforge_youtube_quota_remaining` (Grafana: Channel Performance or
  Infra dashboard) — the `YTForgeQuotaNearExhaustion` alert fires once a
  channel drops below one upload's worth of headroom (1,600 units).
  There's no admin action to "add more quota" short-term; it resets daily
  on Google's side. If a channel is chronically hitting the ceiling,
  either publish less on that channel or request a quota increase from
  Google (a manual process on their end, outside this app).

## Project budgets

Each project can carry an optional `budget_usd`. Agents check
`application/common/budget_meter.py`'s `check_budget` (sums
`prompt_runs.cost_usd`, this codebase's per-provider-call cost record)
before an expensive provider call and should route to review instead of
spending further once exhausted. A project with no `budget_usd` set is
unbounded — set one via the project's settings if you want spend capped.
Provider Costs dashboard (Grafana) shows spend by provider/capability, but
**not** currently broken out by project — cross-reference `prompt_runs`
directly (or the project's own Scripts/Assets pages) if you need
per-project spend during an investigation.

## Model registry & provider discovery

`GET /models` lists every registered model (cloud + local). Local
model servers (Ollama, LM Studio, ComfyUI) are discovered automatically at
boot and periodically (`infrastructure/providers/discovery.py`) — a
server that's down simply doesn't get registered/updated, it doesn't crash
anything. `PATCH /models/{entry_id}/status` lets you manually disable a
model (e.g. taking a flaky provider out of the `ModelRouter`'s fallback
chain without waiting for discovery to notice).

## Incident response

| Symptom | Where to look | Likely cause |
|---|---|---|
| `YTForgePipelineJobFailure` firing | Temporal UI for the workflow, `jobs` table's `error` column | Provider outage, unhandled exception in an activity — check the activity's structured logs (trace-correlated if the `observability` profile is up) |
| `YTForgeDlqGrowth` firing | Redis `events:dlq` stream entries (each carries the original event fields + `error`) | A specific event handler is failing repeatedly — the error field names the exception; the event itself is preserved, so once fixed you can manually replay it |
| `YTForgeProviderErrorRateSpike` firing | Provider Costs dashboard, structured `provider_call` logs (Loki, if `observability` up) | Provider outage or API contract change — the model registry lets you disable that provider/model without a deploy while you investigate |
| `YTForgeQuotaNearExhaustion` firing | Channel Performance / Infra dashboard | Expected under heavy publish volume — no action needed unless it's blocking a scheduled publish, see Channels above |
| Approval stuck, no workflow progress | Temporal UI | Workflow may have failed before reaching the approval-request activity — check its event history, not just the `approvals` table |

## Backup & restore

- **Postgres** holds everything transactional: users, channels (encrypted
  tokens), projects, scripts, jobs, approvals, audit logs, analytics.
  Standard `pg_dump`/`pg_basebackup` against the `postgres` service's
  volume; this is the backup that matters most.
- **MinIO** holds generated media (images, video, voiceovers, renders) —
  back up the `minio_data` volume or replicate the bucket to external
  object storage; losing it doesn't lose the pipeline's record of what
  *should* exist (that's in Postgres), only the actual media files.
  Deleted assets are already soft-deleted (`orphan_asset`), never a hard
  delete triggered by this app itself.
- **`ENCRYPTION_MASTER_KEY`** is not in Postgres — it's an environment
  secret. Losing it makes every stored `oauth_refresh_token` permanently
  undecryptable (every channel needs re-linking). Back this up separately
  from the database, in whatever secret manager holds your other
  production secrets.
- Temporal's own state (workflow history) lives in Postgres too (the
  `temporal` service's own database, distinct from the app's `ytforge`
  database) — include it in the same backup cadence if you need to
  recover in-flight pipelines, not just completed data.
