from __future__ import annotations

from ytforge.interfaces.workflows.analytics_cron import (
    AnalyticsCronWorkflow,
    AnalyticsCronWorkflowInput,
    AnalyticsCronWorkflowOutput,
)
from ytforge.interfaces.workflows.scheduled_publish import (
    ScheduledPublishWorkflow,
    ScheduledPublishWorkflowInput,
    ScheduledPublishWorkflowOutput,
)
from ytforge.interfaces.workflows.trend_discovery_cron import (
    TrendDiscoveryCronWorkflow,
    TrendDiscoveryCronWorkflowInput,
    TrendDiscoveryCronWorkflowOutput,
)
from ytforge.interfaces.workflows.video_production import (
    VideoProductionWorkflow,
    VideoProductionWorkflowInput,
    VideoProductionWorkflowOutput,
)

ALL_WORKFLOWS = [
    VideoProductionWorkflow,
    ScheduledPublishWorkflow,
    AnalyticsCronWorkflow,
    TrendDiscoveryCronWorkflow,
]

__all__ = [
    "ALL_WORKFLOWS",
    "AnalyticsCronWorkflow",
    "AnalyticsCronWorkflowInput",
    "AnalyticsCronWorkflowOutput",
    "ScheduledPublishWorkflow",
    "ScheduledPublishWorkflowInput",
    "ScheduledPublishWorkflowOutput",
    "TrendDiscoveryCronWorkflow",
    "TrendDiscoveryCronWorkflowInput",
    "TrendDiscoveryCronWorkflowOutput",
    "VideoProductionWorkflow",
    "VideoProductionWorkflowInput",
    "VideoProductionWorkflowOutput",
]
