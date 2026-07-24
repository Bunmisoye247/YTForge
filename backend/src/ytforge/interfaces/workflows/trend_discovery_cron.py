from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

from ytforge.interfaces.activity_dto import (
    FetchCandidateTopicsActivityInput,
    FetchCandidateTopicsActivityOutput,
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
_TOPICS_LIMIT = 10


@dataclass(frozen=True, slots=True)
class TrendDiscoveryCronWorkflowInput:
    channel_id: str
    project_id: str
    job_id: str | None = None


@dataclass(frozen=True, slots=True)
class TrendDiscoveryCronWorkflowOutput:
    ok: bool
    error: str | None = None


@workflow.defn(name="TrendDiscoveryCronWorkflow")
class TrendDiscoveryCronWorkflow:
    """ARCHITECTURE.md §5.1's standalone TrendDiscovery cron (the box that
    branches off before Research in the main pipeline diagram, run
    independently rather than as part of `VideoProductionWorkflow`).
    Fetches real candidate topics via the Hacker News source (see
    `infrastructure/external/trends_sources/hackernews.py` — the one real,
    keyless source built for Phase 7; the other 6 named in the
    `TrendSource` enum are follow-up work), scores them via `TrendAgent`,
    then reschedules itself daily via `continue_as_new` indefinitely —
    unlike `AnalyticsCronWorkflow` this has no day-count limit, matching
    the architecture diagram's "standalone cron" (not tied to a single
    video's lifecycle).

    `TrendAgent` requires a `project_id` to look up the channel
    (`ctx.uow.projects.get_by_id`) — this workflow takes one explicitly
    rather than creating projects itself, since project creation isn't
    this workflow's job."""

    @workflow.run
    async def run(self, data: TrendDiscoveryCronWorkflowInput) -> TrendDiscoveryCronWorkflowOutput:
        info = workflow.info()
        if data.job_id is not None:
            job_id = data.job_id
        else:
            job: RecordJobStartedActivityOutput = await workflow.execute_activity(
                "record_job_started",
                RecordJobStartedActivityInput(
                    workflow_id=info.workflow_id,
                    run_id=info.run_id,
                    workflow_type="TrendDiscoveryCronWorkflow",
                    project_id=data.project_id,
                ),
                start_to_close_timeout=_QUICK_TIMEOUT,
                result_type=RecordJobStartedActivityOutput,
            )
            job_id = job.job_id

        try:
            topics: FetchCandidateTopicsActivityOutput = await workflow.execute_activity(
                "fetch_candidate_topics",
                FetchCandidateTopicsActivityInput(limit=_TOPICS_LIMIT),
                start_to_close_timeout=_QUICK_TIMEOUT,
                retry_policy=_DEFAULT_RETRY,
                result_type=FetchCandidateTopicsActivityOutput,
            )

            result: RunAgentOutput = await workflow.execute_activity(
                "run_agent",
                RunAgentInput(
                    agent_name="trend", project_id=data.project_id, payload={"candidate_topics": topics.topics}
                ),
                start_to_close_timeout=_AGENT_STEP_TIMEOUT,
                retry_policy=_DEFAULT_RETRY,
                result_type=RunAgentOutput,
            )
            if not result.ok:
                raise ApplicationError(f"trend agent failed: {result.error}")

        except Exception as exc:
            await workflow.execute_activity(
                "update_job_status",
                UpdateJobStatusActivityInput(job_id=job_id, status="failed", error=str(exc)),
                start_to_close_timeout=_QUICK_TIMEOUT,
            )
            return TrendDiscoveryCronWorkflowOutput(ok=False, error=str(exc))

        await workflow.sleep(_POLL_INTERVAL)
        workflow.continue_as_new(
            TrendDiscoveryCronWorkflowInput(channel_id=data.channel_id, project_id=data.project_id, job_id=job_id)
        )
