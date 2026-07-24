from __future__ import annotations

from ytforge.infrastructure.db.repositories.analytics import (
    SqlAlchemyAnalyticsDailyMetricRepository,
    SqlAlchemyAnalyticsRetentionPointRepository,
    SqlAlchemyAnalyticsTrafficSourceRepository,
)
from ytforge.infrastructure.db.repositories.approvals import SqlAlchemyApprovalRepository
from ytforge.infrastructure.db.repositories.assets import SqlAlchemyAssetRepository
from ytforge.infrastructure.db.repositories.audit import SqlAlchemyAuditLogRepository
from ytforge.infrastructure.db.repositories.channels import (
    SqlAlchemyChannelMemberRepository,
    SqlAlchemyChannelRepository,
)
from ytforge.infrastructure.db.repositories.fact_checks import SqlAlchemyFactCheckRepository
from ytforge.infrastructure.db.repositories.jobs import SqlAlchemyJobRepository
from ytforge.infrastructure.db.repositories.model_registry import (
    SqlAlchemyModelRegistryRepository,
)
from ytforge.infrastructure.db.repositories.outbox import SqlAlchemyOutboxRepository
from ytforge.infrastructure.db.repositories.projects import SqlAlchemyProjectRepository
from ytforge.infrastructure.db.repositories.prompts import (
    SqlAlchemyPromptRunRepository,
    SqlAlchemyPromptTemplateRepository,
    SqlAlchemyPromptVersionRepository,
)
from ytforge.infrastructure.db.repositories.quota import SqlAlchemyApiQuotaLedgerRepository
from ytforge.infrastructure.db.repositories.research import (
    SqlAlchemyResearchDocumentRepository,
)
from ytforge.infrastructure.db.repositories.scripts import SqlAlchemyScriptRepository
from ytforge.infrastructure.db.repositories.storyboards import (
    SqlAlchemySceneRepository,
    SqlAlchemyStoryboardRepository,
)
from ytforge.infrastructure.db.repositories.trends import SqlAlchemyTrendRepository
from ytforge.infrastructure.db.repositories.users import SqlAlchemyUserRepository
from ytforge.infrastructure.db.repositories.videos import (
    SqlAlchemySeoMetadataRepository,
    SqlAlchemyVideoRepository,
)
from ytforge.infrastructure.db.repositories.voice import (
    SqlAlchemyVoiceoverRepository,
    SqlAlchemyVoiceProfileRepository,
)

__all__ = [
    "SqlAlchemyAnalyticsDailyMetricRepository",
    "SqlAlchemyAnalyticsRetentionPointRepository",
    "SqlAlchemyAnalyticsTrafficSourceRepository",
    "SqlAlchemyApiQuotaLedgerRepository",
    "SqlAlchemyApprovalRepository",
    "SqlAlchemyAssetRepository",
    "SqlAlchemyAuditLogRepository",
    "SqlAlchemyChannelMemberRepository",
    "SqlAlchemyChannelRepository",
    "SqlAlchemyFactCheckRepository",
    "SqlAlchemyJobRepository",
    "SqlAlchemyModelRegistryRepository",
    "SqlAlchemyOutboxRepository",
    "SqlAlchemyProjectRepository",
    "SqlAlchemyPromptRunRepository",
    "SqlAlchemyPromptTemplateRepository",
    "SqlAlchemyPromptVersionRepository",
    "SqlAlchemyResearchDocumentRepository",
    "SqlAlchemySceneRepository",
    "SqlAlchemyScriptRepository",
    "SqlAlchemySeoMetadataRepository",
    "SqlAlchemyStoryboardRepository",
    "SqlAlchemyTrendRepository",
    "SqlAlchemyUserRepository",
    "SqlAlchemyVideoRepository",
    "SqlAlchemyVoiceoverRepository",
    "SqlAlchemyVoiceProfileRepository",
]
