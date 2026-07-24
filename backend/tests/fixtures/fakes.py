from __future__ import annotations

import uuid
from datetime import UTC, datetime
from datetime import date as date_
from decimal import Decimal
from types import TracebackType
from typing import Any

from uuid6 import uuid7

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import DecodedToken
from ytforge.domain.entities import (
    AnalyticsDailyMetric,
    AnalyticsRetentionPoint,
    AnalyticsTrafficSource,
    ApiQuotaLedger,
    Approval,
    Asset,
    AuditLog,
    Channel,
    ChannelMember,
    FactCheck,
    Job,
    ModelRegistryEntry,
    OutboxEvent,
    Project,
    PromptRun,
    PromptTemplate,
    PromptVersion,
    ResearchDocument,
    Scene,
    Script,
    SeoMetadata,
    Storyboard,
    Trend,
    User,
    Video,
    Voiceover,
    VoiceProfile,
)
from ytforge.domain.enums import ApprovalStatus, OutboxStatus


class _FakeCrudRepository[TEntity]:
    """A minimal in-memory stand-in shared by the fake per-aggregate repos
    below — good enough for exercising use-case control flow without a DB."""

    def __init__(self) -> None:
        self.items: dict[uuid.UUID, TEntity] = {}

    async def add(self, entity: TEntity) -> None:
        self.items[entity.id] = entity  # type: ignore[attr-defined]

    async def update(self, entity: TEntity) -> None:
        self.items[entity.id] = entity  # type: ignore[attr-defined]


class FakeUserRepository(_FakeCrudRepository[User]):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.items.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.items.values() if u.email == email), None)


class FakeChannelRepository(_FakeCrudRepository[Channel]):
    async def get_by_id(self, channel_id: uuid.UUID) -> Channel | None:
        return self.items.get(channel_id)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Channel]:
        return list(self.items.values())


class FakeChannelMemberRepository(_FakeCrudRepository[ChannelMember]):
    async def get(self, channel_id: uuid.UUID, user_id: uuid.UUID) -> ChannelMember | None:
        return next(
            (m for m in self.items.values() if m.channel_id == channel_id and m.user_id == user_id),
            None,
        )

    async def list_for_channel(self, channel_id: uuid.UUID) -> list[ChannelMember]:
        return [m for m in self.items.values() if m.channel_id == channel_id]


class FakeProjectRepository(_FakeCrudRepository[Project]):
    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        return self.items.get(project_id)

    async def list_for_channel(self, channel_id: uuid.UUID, params: PageParams) -> Page[Project]:
        matches = [p for p in self.items.values() if p.channel_id == channel_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeTrendRepository(_FakeCrudRepository[Trend]):
    async def get_by_id(self, trend_id: uuid.UUID) -> Trend | None:
        return self.items.get(trend_id)

    async def list_for_channel(self, channel_id: uuid.UUID, params: PageParams) -> Page[Trend]:
        matches = [t for t in self.items.values() if t.channel_id == channel_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeResearchDocumentRepository(_FakeCrudRepository[ResearchDocument]):
    async def get_by_id(self, document_id: uuid.UUID) -> ResearchDocument | None:
        return self.items.get(document_id)

    async def list_for_project(
        self, project_id: uuid.UUID, params: PageParams
    ) -> Page[ResearchDocument]:
        matches = [d for d in self.items.values() if d.project_id == project_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeScriptRepository(_FakeCrudRepository[Script]):
    async def get_by_id(self, script_id: uuid.UUID) -> Script | None:
        return self.items.get(script_id)

    async def get_latest_for_project(self, project_id: uuid.UUID) -> Script | None:
        matches = sorted(
            (s for s in self.items.values() if s.project_id == project_id),
            key=lambda s: s.version,
            reverse=True,
        )
        return matches[0] if matches else None

    async def list_for_project(self, project_id: uuid.UUID, params: PageParams) -> Page[Script]:
        matches = [s for s in self.items.values() if s.project_id == project_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeFactCheckRepository(_FakeCrudRepository[FactCheck]):
    async def list_for_script(self, script_id: uuid.UUID) -> list[FactCheck]:
        return [f for f in self.items.values() if f.script_id == script_id]


class FakeStoryboardRepository(_FakeCrudRepository[Storyboard]):
    async def get_by_id(self, storyboard_id: uuid.UUID) -> Storyboard | None:
        return self.items.get(storyboard_id)

    async def get_by_project(self, project_id: uuid.UUID) -> Storyboard | None:
        return next((s for s in self.items.values() if s.project_id == project_id), None)


class FakeSceneRepository(_FakeCrudRepository[Scene]):
    async def get_by_id(self, scene_id: uuid.UUID) -> Scene | None:
        return self.items.get(scene_id)

    async def list_for_storyboard(self, storyboard_id: uuid.UUID) -> list[Scene]:
        return sorted(
            (s for s in self.items.values() if s.storyboard_id == storyboard_id),
            key=lambda s: s.sequence_index,
        )


class FakeAssetRepository(_FakeCrudRepository[Asset]):
    async def get_by_id(self, asset_id: uuid.UUID) -> Asset | None:
        return self.items.get(asset_id)

    async def list_for_project(self, project_id: uuid.UUID, params: PageParams) -> Page[Asset]:
        matches = [a for a in self.items.values() if a.project_id == project_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeVoiceProfileRepository(_FakeCrudRepository[VoiceProfile]):
    async def get_by_id(self, voice_profile_id: uuid.UUID) -> VoiceProfile | None:
        return self.items.get(voice_profile_id)

    async def list_for_channel(self, channel_id: uuid.UUID) -> list[VoiceProfile]:
        return [p for p in self.items.values() if p.channel_id == channel_id]


class FakeVoiceoverRepository(_FakeCrudRepository[Voiceover]):
    async def list_for_project(self, project_id: uuid.UUID) -> list[Voiceover]:
        return [v for v in self.items.values() if v.project_id == project_id]


class FakePromptTemplateRepository(_FakeCrudRepository[PromptTemplate]):
    async def get_by_id(self, template_id: uuid.UUID) -> PromptTemplate | None:
        return self.items.get(template_id)

    async def get_by_agent_and_name(self, agent: str, name: str) -> PromptTemplate | None:
        return next(
            (t for t in self.items.values() if t.agent == agent and t.name == name), None
        )

    async def list_all(self) -> list[PromptTemplate]:
        return list(self.items.values())


class FakePromptVersionRepository(_FakeCrudRepository[PromptVersion]):
    async def get_latest(self, template_id: uuid.UUID) -> PromptVersion | None:
        matches = sorted(
            (v for v in self.items.values() if v.template_id == template_id),
            key=lambda v: v.version,
            reverse=True,
        )
        return matches[0] if matches else None

    async def list_for_template(self, template_id: uuid.UUID) -> list[PromptVersion]:
        return [v for v in self.items.values() if v.template_id == template_id]


class FakePromptRunRepository(_FakeCrudRepository[PromptRun]):
    async def list_for_version(
        self, prompt_version_id: uuid.UUID, params: PageParams
    ) -> Page[PromptRun]:
        matches = [r for r in self.items.values() if r.prompt_version_id == prompt_version_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)

    async def sum_cost_for_project(self, project_id: uuid.UUID) -> Decimal:
        return sum(
            (r.cost_usd for r in self.items.values() if r.project_id == project_id and r.cost_usd),
            Decimal("0"),
        )


class FakeVideoRepository(_FakeCrudRepository[Video]):
    async def get_by_id(self, video_id: uuid.UUID) -> Video | None:
        return self.items.get(video_id)

    async def list_for_project(self, project_id: uuid.UUID, params: PageParams) -> Page[Video]:
        matches = [v for v in self.items.values() if v.project_id == project_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeSeoMetadataRepository(_FakeCrudRepository[SeoMetadata]):
    async def get_for_video(self, video_id: uuid.UUID) -> SeoMetadata | None:
        return next((s for s in self.items.values() if s.video_id == video_id), None)


class FakeApprovalRepository(_FakeCrudRepository[Approval]):
    async def get_by_id(self, approval_id: uuid.UUID) -> Approval | None:
        return self.items.get(approval_id)

    async def list_by_status(
        self, status: ApprovalStatus | None, params: PageParams
    ) -> Page[Approval]:
        matches = [a for a in self.items.values() if status is None or a.status == status]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeAnalyticsDailyMetricRepository(_FakeCrudRepository[AnalyticsDailyMetric]):
    async def upsert(self, metric: AnalyticsDailyMetric) -> None:
        key = next(
            (k for k, v in self.items.items() if v.video_id == metric.video_id and v.date == metric.date),
            metric.id,
        )
        self.items[key] = metric

    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsDailyMetric]:
        return [m for m in self.items.values() if m.video_id == video_id]


class FakeAnalyticsRetentionPointRepository(_FakeCrudRepository[AnalyticsRetentionPoint]):
    async def upsert(self, point: AnalyticsRetentionPoint) -> None:
        self.items[point.id] = point

    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsRetentionPoint]:
        return [p for p in self.items.values() if p.video_id == video_id]


class FakeAnalyticsTrafficSourceRepository(_FakeCrudRepository[AnalyticsTrafficSource]):
    async def upsert(self, source: AnalyticsTrafficSource) -> None:
        self.items[source.id] = source

    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsTrafficSource]:
        return [s for s in self.items.values() if s.video_id == video_id]


class FakeModelRegistryRepository(_FakeCrudRepository[ModelRegistryEntry]):
    async def get_by_id(self, entry_id: uuid.UUID) -> ModelRegistryEntry | None:
        return self.items.get(entry_id)

    async def list_all(self) -> list[ModelRegistryEntry]:
        return list(self.items.values())


class FakeApiQuotaLedgerRepository(_FakeCrudRepository[ApiQuotaLedger]):
    async def list_for_channel(
        self, channel_id: uuid.UUID, start: date_, end: date_
    ) -> list[ApiQuotaLedger]:
        return [
            e
            for e in self.items.values()
            if e.channel_id == channel_id and start <= e.date <= end
        ]


class FakeJobRepository(_FakeCrudRepository[Job]):
    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        return self.items.get(job_id)

    async def list_for_project(
        self, project_id: uuid.UUID | None, params: PageParams
    ) -> Page[Job]:
        matches = [j for j in self.items.values() if project_id is None or j.project_id == project_id]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeAuditLogRepository(_FakeCrudRepository[AuditLog]):
    async def list_for_entity(
        self, entity_type: str, entity_id: uuid.UUID, params: PageParams
    ) -> Page[AuditLog]:
        matches = [
            a for a in self.items.values() if a.entity_type == entity_type and a.entity_id == entity_id
        ]
        page_items = matches[params.offset : params.offset + params.limit]
        return Page(items=page_items, total=len(matches), limit=params.limit, offset=params.offset)


class FakeOutboxRepository(_FakeCrudRepository[OutboxEvent]):
    async def list_pending(self, limit: int = 100) -> list[OutboxEvent]:
        pending = [e for e in self.items.values() if e.status == OutboxStatus.PENDING]
        return sorted(pending, key=lambda e: e.created_at)[:limit]

    async def mark_published(self, event_id: uuid.UUID) -> None:
        self.items[event_id].status = OutboxStatus.PUBLISHED
        self.items[event_id].published_at = datetime.now(UTC)

    async def mark_failed(self, event_id: uuid.UUID) -> None:
        self.items[event_id].status = OutboxStatus.FAILED


class FakeUnitOfWork:
    """In-memory UnitOfWork for application-layer tests — no DB, no I/O."""

    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.channels = FakeChannelRepository()
        self.channel_members = FakeChannelMemberRepository()
        self.projects = FakeProjectRepository()
        self.trends = FakeTrendRepository()
        self.research_documents = FakeResearchDocumentRepository()
        self.scripts = FakeScriptRepository()
        self.fact_checks = FakeFactCheckRepository()
        self.storyboards = FakeStoryboardRepository()
        self.scenes = FakeSceneRepository()
        self.assets = FakeAssetRepository()
        self.voice_profiles = FakeVoiceProfileRepository()
        self.voiceovers = FakeVoiceoverRepository()
        self.prompt_templates = FakePromptTemplateRepository()
        self.prompt_versions = FakePromptVersionRepository()
        self.prompt_runs = FakePromptRunRepository()
        self.videos = FakeVideoRepository()
        self.seo_metadata = FakeSeoMetadataRepository()
        self.approvals = FakeApprovalRepository()
        self.analytics_daily_metrics = FakeAnalyticsDailyMetricRepository()
        self.analytics_retention_points = FakeAnalyticsRetentionPointRepository()
        self.analytics_traffic_sources = FakeAnalyticsTrafficSourceRepository()
        self.model_registry = FakeModelRegistryRepository()
        self.api_quota_ledger = FakeApiQuotaLedgerRepository()
        self.jobs = FakeJobRepository()
        self.audit_logs = FakeAuditLogRepository()
        self.outbox = FakeOutboxRepository()
        self.events: list[dict[str, Any]] = []
        self.committed = False

    async def __aenter__(self) -> FakeUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass

    async def add_event(
        self, *, aggregate_type: str, aggregate_id: uuid.UUID, event_type: str, payload: dict[str, Any]
    ) -> None:
        self.events.append(
            {
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "event_type": event_type,
                "payload": payload,
            }
        )
        now = datetime.now(UTC)
        event_id = uuid7()
        self.outbox.items[event_id] = OutboxEvent(
            id=event_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            status=OutboxStatus.PENDING,
            created_at=now,
            updated_at=now,
            payload=payload,
        )


class FakePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hashed: str) -> bool:
        return hashed == f"hashed:{password}"


class FakeTokenService:
    def __init__(self) -> None:
        self.issued_access: dict[str, uuid.UUID] = {}
        self.issued_refresh: dict[str, tuple[uuid.UUID, int]] = {}
        self._counter = 0

    def _next_token(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter}"

    def issue_access_token(self, user_id: uuid.UUID) -> str:
        token = self._next_token("access")
        self.issued_access[token] = user_id
        return token

    def issue_refresh_token(self, user_id: uuid.UUID, token_version: int) -> str:
        token = self._next_token("refresh")
        self.issued_refresh[token] = (user_id, token_version)
        return token

    def decode_access_token(self, token: str) -> DecodedToken:
        user_id = self.issued_access[token]
        return DecodedToken(user_id=user_id, token_version=-1)

    def decode_refresh_token(self, token: str) -> DecodedToken:
        user_id, token_version = self.issued_refresh[token]
        return DecodedToken(user_id=user_id, token_version=token_version)
