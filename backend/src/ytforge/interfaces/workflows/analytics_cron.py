from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from ytforge.interfaces.activity_dto import (
    IngestAnalyticsActivityInput,
    IngestAnalyticsActivityOutput,
    RecordJobStartedActivityInput,
    RecordJobStartedActivityOutput,
    RunAgentInput,
    RunAgentOutput,
    UpdateJobStatusActivityInput,
)

_AGENT_STEP_TIMEOUT = timedelta(minutes=10)
_QUICK_TIMEOUT = timedelta(seconds=30)
_DEFAULT_RETRY = RetryPolicy(maximum_attempts=3)
_POLL_INTERVAL = timedelta(hours=24)


@dataclass(frozen=True, slots=True)
class AnalyticsCronWorkflowInput:
    project_id: str
    video_id: str
    remaining_days: int = 30
    job_id: str | None = None


@dataclass(frozen=True, slots=True)
class AnalyticsCronWorkflowOutput:
    ok: bool
    days_run: int


@workflow.defn(name="AnalyticsCronWorkflow")
class AnalyticsCronWorkflow:
    """ARCHITECTURE.md §5.1's "Analytics collection (cron child, 30 days)"
    stage. Each iteration first pulls real YouTube Analytics metrics for
    "yesterday" via the `ingest_analytics` activity (Phase 8 — resolves
    the video's channel/refresh-token from `video_id` alone, so nothing
    secret needs to survive `continue_as_new`), then runs the existing
    `AnalyticsAgent` against the now-current `analytics_daily_metric`
    rows — once a day, for `remaining_days` days, via `continue_as_new`
    (keeps workflow history bounded rather than growing unboundedly over
    30 iterations in a single run's history, per Temporal best practice).

    Job tracking: `record_job_started` is only called on the FIRST
    iteration (`data.job_id is None`) — every `continue_as_new` carries
    the same `job_id` forward as input, rather than creating a new `jobs`
    row per day. That job row is marked completed only once
    `remaining_days` reaches zero, or failed if an iteration's agent run
    fails outright."""

    @workflow.run
    async def run(self, data: AnalyticsCronWorkflowInput) -> AnalyticsCronWorkflowOutput:
        info = workflow.info()
        if data.job_id is not None:
            job_id = data.job_id
        else:
            job: RecordJobStartedActivityOutput = await workflow.execute_activity(
                "record_job_started",
                RecordJobStartedActivityInput(
                    workflow_id=info.workflow_id,
                    run_id=info.run_id,
                    workflow_type="AnalyticsCronWorkflow",
                    project_id=data.project_id,
                ),
                start_to_close_timeout=_QUICK_TIMEOUT,
                result_type=RecordJobStartedActivityOutput,
            )
            job_id = job.job_id

        # `ingested=False` means the video isn't published yet or its
        # channel isn't linked — not an error, `AnalyticsAgent` below will
        # just fail its own "no analytics ingested yet" check instead.
        target_date = (workflow.now() - timedelta(days=1)).date()
        await workflow.execute_activity(
            "ingest_analytics",
            IngestAnalyticsActivityInput(video_id=data.video_id, target_date_iso=target_date.isoformat()),
            start_to_close_timeout=_QUICK_TIMEOUT,
            retry_policy=_DEFAULT_RETRY,
            result_type=IngestAnalyticsActivityOutput,
        )

        result: RunAgentOutput = await workflow.execute_activity(
            "run_agent",
            RunAgentInput(agent_name="analytics", project_id=data.project_id, payload={"video_id": data.video_id}),
            start_to_close_timeout=_AGENT_STEP_TIMEOUT,
            retry_policy=_DEFAULT_RETRY,
            result_type=RunAgentOutput,
        )
        if not result.ok:
            await workflow.execute_activity(
                "update_job_status",
                UpdateJobStatusActivityInput(job_id=job_id, status="failed", error=result.error),
                start_to_close_timeout=_QUICK_TIMEOUT,
            )
            return AnalyticsCronWorkflowOutput(ok=False, days_run=30 - data.remaining_days + 1)

        if data.remaining_days <= 1:
            await workflow.execute_activity(
                "update_job_status",
                UpdateJobStatusActivityInput(job_id=job_id, status="completed"),
                start_to_close_timeout=_QUICK_TIMEOUT,
            )
            return AnalyticsCronWorkflowOutput(ok=True, days_run=30)

        await workflow.sleep(_POLL_INTERVAL)
        workflow.continue_as_new(
            AnalyticsCronWorkflowInput(
                project_id=data.project_id,
                video_id=data.video_id,
                remaining_days=data.remaining_days - 1,
                job_id=job_id,
            )
        )
