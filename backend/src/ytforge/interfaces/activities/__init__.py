from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ytforge.interfaces.activities.agent_activities import run_agent_activity
from ytforge.interfaces.activities.pipeline_activities import (
    check_budget_activity,
    create_video_activity,
    emit_event_activity,
    fetch_candidate_topics_activity,
    ingest_analytics_activity,
    orphan_assets_activity,
    record_job_started_activity,
    request_approval_activity,
    request_publish_approval_activity,
    update_job_status_activity,
)

ALL_ACTIVITIES: list[Callable[..., Any]] = [
    run_agent_activity,
    record_job_started_activity,
    update_job_status_activity,
    emit_event_activity,
    request_approval_activity,
    request_publish_approval_activity,
    orphan_assets_activity,
    create_video_activity,
    check_budget_activity,
    fetch_candidate_topics_activity,
    ingest_analytics_activity,
]

__all__ = [
    "ALL_ACTIVITIES",
    "check_budget_activity",
    "create_video_activity",
    "emit_event_activity",
    "fetch_candidate_topics_activity",
    "ingest_analytics_activity",
    "orphan_assets_activity",
    "record_job_started_activity",
    "request_approval_activity",
    "request_publish_approval_activity",
    "run_agent_activity",
    "update_job_status_activity",
]
