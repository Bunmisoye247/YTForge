from __future__ import annotations

import uuid
from types import TracebackType
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ytforge.domain.enums import OutboxStatus
from ytforge.infrastructure.db.models import OutboxEvent
from ytforge.infrastructure.db.repositories import (
    SqlAlchemyAnalyticsDailyMetricRepository,
    SqlAlchemyAnalyticsRetentionPointRepository,
    SqlAlchemyAnalyticsTrafficSourceRepository,
    SqlAlchemyApiQuotaLedgerRepository,
    SqlAlchemyApprovalRepository,
    SqlAlchemyAssetRepository,
    SqlAlchemyAuditLogRepository,
    SqlAlchemyChannelMemberRepository,
    SqlAlchemyChannelRepository,
    SqlAlchemyFactCheckRepository,
    SqlAlchemyJobRepository,
    SqlAlchemyModelRegistryRepository,
    SqlAlchemyOutboxRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyPromptRunRepository,
    SqlAlchemyPromptTemplateRepository,
    SqlAlchemyPromptVersionRepository,
    SqlAlchemyResearchDocumentRepository,
    SqlAlchemySceneRepository,
    SqlAlchemyScriptRepository,
    SqlAlchemySeoMetadataRepository,
    SqlAlchemyStoryboardRepository,
    SqlAlchemyTrendRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyVideoRepository,
    SqlAlchemyVoiceoverRepository,
    SqlAlchemyVoiceProfileRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        session = self._session

        self.users = SqlAlchemyUserRepository(session)
        self.channels = SqlAlchemyChannelRepository(session)
        self.channel_members = SqlAlchemyChannelMemberRepository(session)
        self.projects = SqlAlchemyProjectRepository(session)
        self.trends = SqlAlchemyTrendRepository(session)
        self.research_documents = SqlAlchemyResearchDocumentRepository(session)
        self.scripts = SqlAlchemyScriptRepository(session)
        self.fact_checks = SqlAlchemyFactCheckRepository(session)
        self.storyboards = SqlAlchemyStoryboardRepository(session)
        self.scenes = SqlAlchemySceneRepository(session)
        self.assets = SqlAlchemyAssetRepository(session)
        self.voice_profiles = SqlAlchemyVoiceProfileRepository(session)
        self.voiceovers = SqlAlchemyVoiceoverRepository(session)
        self.prompt_templates = SqlAlchemyPromptTemplateRepository(session)
        self.prompt_versions = SqlAlchemyPromptVersionRepository(session)
        self.prompt_runs = SqlAlchemyPromptRunRepository(session)
        self.videos = SqlAlchemyVideoRepository(session)
        self.seo_metadata = SqlAlchemySeoMetadataRepository(session)
        self.approvals = SqlAlchemyApprovalRepository(session)
        self.analytics_daily_metrics = SqlAlchemyAnalyticsDailyMetricRepository(session)
        self.analytics_retention_points = SqlAlchemyAnalyticsRetentionPointRepository(session)
        self.analytics_traffic_sources = SqlAlchemyAnalyticsTrafficSourceRepository(session)
        self.model_registry = SqlAlchemyModelRegistryRepository(session)
        self.api_quota_ledger = SqlAlchemyApiQuotaLedgerRepository(session)
        self.jobs = SqlAlchemyJobRepository(session)
        self.audit_logs = SqlAlchemyAuditLogRepository(session)
        self.outbox = SqlAlchemyOutboxRepository(session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        if exc_type is not None:
            await self._session.rollback()
        await self._session.close()
        self._session = None

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None
        await self._session.rollback()

    async def add_event(
        self,
        *,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        assert self._session is not None
        self._session.add(
            OutboxEvent(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=payload,
                status=OutboxStatus.PENDING,
            )
        )
        await self._session.flush()
