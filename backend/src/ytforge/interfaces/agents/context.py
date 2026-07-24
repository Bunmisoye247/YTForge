from __future__ import annotations

from dataclasses import dataclass

from ytforge.application.ports.providers import ModelRouter, PromptTemplateStore, UnitOfWork
from ytforge.application.ports.providers.editing_pipeline import EditingPipeline
from ytforge.application.ports.providers.object_storage import ObjectStorage
from ytforge.application.ports.providers.vector_store import VectorStore
from ytforge.application.ports.providers.youtube_gateway import YouTubeGateway
from ytforge.interfaces.agents.tools import ToolRegistry


@dataclass(slots=True)
class AgentContext:
    """ARCHITECTURE.md §3: "the routed LLM (via ModelRouter), tool
    registry, prompt template store, budget/token meter, and the event
    emitter." Budget checking is `application.common.budget_meter
    .check_budget(ctx.uow, project_id)` rather than a separate object here
    — it only ever needs `uow` + a project id, so a stateful field would be
    redundant. The event emitter is `ctx.uow.add_event(...)`, the same
    transactional-outbox mechanism every Phase-4 use case already uses.
    `vector_store` is separate from `uow` — Qdrant isn't part of the
    Postgres unit-of-work/transaction boundary. `object_storage` (Phase 7)
    is how media-producing agents persist provider bytes into MinIO instead
    of returning a placeholder key. `editing_pipeline` and `youtube_gateway`
    back `EditingAgent`/`PublisherAgent` — both real as of Phase 7 (FFmpeg
    renderer) and Phase 8 (YouTube Data API v3) respectively.
    `youtube_upload_quota_cost`/`youtube_daily_quota_budget` are plain
    config `PublisherAgent` needs to check/debit `api_quota_ledger`
    (ARCHITECTURE.md §8) — not a port, just numbers, so no dedicated
    object for them."""

    model_router: ModelRouter
    tools: ToolRegistry
    prompts: PromptTemplateStore
    uow: UnitOfWork
    vector_store: VectorStore
    object_storage: ObjectStorage
    editing_pipeline: EditingPipeline
    youtube_gateway: YouTubeGateway
    youtube_upload_quota_cost: int = 1600
    youtube_daily_quota_budget: int = 10000
