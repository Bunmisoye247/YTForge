from __future__ import annotations

import uuid
from types import TracebackType
from typing import Any, Protocol

from ytforge.application.ports.repositories import (
    AnalyticsDailyMetricRepository,
    AnalyticsRetentionPointRepository,
    AnalyticsTrafficSourceRepository,
    ApiQuotaLedgerRepository,
    ApprovalRepository,
    AssetRepository,
    AuditLogRepository,
    ChannelMemberRepository,
    ChannelRepository,
    FactCheckRepository,
    JobRepository,
    ModelRegistryRepository,
    OutboxRepository,
    ProjectRepository,
    PromptRunRepository,
    PromptTemplateRepository,
    PromptVersionRepository,
    ResearchDocumentRepository,
    SceneRepository,
    ScriptRepository,
    SeoMetadataRepository,
    StoryboardRepository,
    TrendRepository,
    UserRepository,
    VideoRepository,
    VoiceoverRepository,
    VoiceProfileRepository,
)


class UnitOfWork(Protocol):
    """Repository accessors are declared as read-only `@property` rather
    than plain attributes: Protocol attribute matching is invariant (the
    implementer's attribute type must match exactly), while `@property`
    matching is covariant — letting `SqlAlchemyUnitOfWork` hold concrete
    `SqlAlchemyXRepository` instances (each a subtype of its port) satisfy
    this Protocol structurally. Without this, only FastAPI's `Depends()`
    indirection (which erases the check) let concrete instances flow as
    `UnitOfWork`; any direct construction outside of FastAPI DI — e.g. the
    `run-agent`/`sync-prompts` CLI commands — failed mypy on assignment."""

    @property
    def users(self) -> UserRepository: ...
    @property
    def channels(self) -> ChannelRepository: ...
    @property
    def channel_members(self) -> ChannelMemberRepository: ...
    @property
    def projects(self) -> ProjectRepository: ...
    @property
    def trends(self) -> TrendRepository: ...
    @property
    def research_documents(self) -> ResearchDocumentRepository: ...
    @property
    def scripts(self) -> ScriptRepository: ...
    @property
    def fact_checks(self) -> FactCheckRepository: ...
    @property
    def storyboards(self) -> StoryboardRepository: ...
    @property
    def scenes(self) -> SceneRepository: ...
    @property
    def assets(self) -> AssetRepository: ...
    @property
    def voice_profiles(self) -> VoiceProfileRepository: ...
    @property
    def voiceovers(self) -> VoiceoverRepository: ...
    @property
    def prompt_templates(self) -> PromptTemplateRepository: ...
    @property
    def prompt_versions(self) -> PromptVersionRepository: ...
    @property
    def prompt_runs(self) -> PromptRunRepository: ...
    @property
    def videos(self) -> VideoRepository: ...
    @property
    def seo_metadata(self) -> SeoMetadataRepository: ...
    @property
    def approvals(self) -> ApprovalRepository: ...
    @property
    def analytics_daily_metrics(self) -> AnalyticsDailyMetricRepository: ...
    @property
    def analytics_retention_points(self) -> AnalyticsRetentionPointRepository: ...
    @property
    def analytics_traffic_sources(self) -> AnalyticsTrafficSourceRepository: ...
    @property
    def model_registry(self) -> ModelRegistryRepository: ...
    @property
    def api_quota_ledger(self) -> ApiQuotaLedgerRepository: ...
    @property
    def jobs(self) -> JobRepository: ...
    @property
    def audit_logs(self) -> AuditLogRepository: ...
    @property
    def outbox(self) -> OutboxRepository: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def add_event(
        self,
        *,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Append a row to the transactional outbox within the same commit
        (ARCHITECTURE.md §2.3). The relay that publishes these to Redis
        Streams is built alongside `infrastructure/events/` in a later phase.
        """
        ...
