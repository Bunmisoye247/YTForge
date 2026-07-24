from __future__ import annotations

from ytforge.application.ports.repositories.analytics import (
    AnalyticsDailyMetricRepository,
    AnalyticsRetentionPointRepository,
    AnalyticsTrafficSourceRepository,
)
from ytforge.application.ports.repositories.approvals import ApprovalRepository
from ytforge.application.ports.repositories.assets import AssetRepository
from ytforge.application.ports.repositories.audit import AuditLogRepository
from ytforge.application.ports.repositories.channels import (
    ChannelMemberRepository,
    ChannelRepository,
)
from ytforge.application.ports.repositories.fact_checks import FactCheckRepository
from ytforge.application.ports.repositories.jobs import JobRepository
from ytforge.application.ports.repositories.model_registry import ModelRegistryRepository
from ytforge.application.ports.repositories.outbox import OutboxRepository
from ytforge.application.ports.repositories.projects import ProjectRepository
from ytforge.application.ports.repositories.prompts import (
    PromptRunRepository,
    PromptTemplateRepository,
    PromptVersionRepository,
)
from ytforge.application.ports.repositories.quota import ApiQuotaLedgerRepository
from ytforge.application.ports.repositories.research import ResearchDocumentRepository
from ytforge.application.ports.repositories.scripts import ScriptRepository
from ytforge.application.ports.repositories.storyboards import (
    SceneRepository,
    StoryboardRepository,
)
from ytforge.application.ports.repositories.trends import TrendRepository
from ytforge.application.ports.repositories.users import UserRepository
from ytforge.application.ports.repositories.videos import (
    SeoMetadataRepository,
    VideoRepository,
)
from ytforge.application.ports.repositories.voice import (
    VoiceoverRepository,
    VoiceProfileRepository,
)

__all__ = [
    "AnalyticsDailyMetricRepository",
    "AnalyticsRetentionPointRepository",
    "AnalyticsTrafficSourceRepository",
    "ApiQuotaLedgerRepository",
    "ApprovalRepository",
    "AssetRepository",
    "AuditLogRepository",
    "ChannelMemberRepository",
    "ChannelRepository",
    "FactCheckRepository",
    "JobRepository",
    "ModelRegistryRepository",
    "OutboxRepository",
    "ProjectRepository",
    "PromptRunRepository",
    "PromptTemplateRepository",
    "PromptVersionRepository",
    "ResearchDocumentRepository",
    "SceneRepository",
    "ScriptRepository",
    "SeoMetadataRepository",
    "StoryboardRepository",
    "TrendRepository",
    "UserRepository",
    "VideoRepository",
    "VoiceoverRepository",
    "VoiceProfileRepository",
]
