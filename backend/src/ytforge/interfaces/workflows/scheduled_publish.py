from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

from ytforge.interfaces.activity_dto import (
    RecordJobStartedActivityInput,
    RecordJobStartedActivityOutput,
    RunAgentInput,
    RunAgentOutput,
    UpdateJobStatusActivityInput,
)

_AGENT_STEP_TIMEOUT = timedelta(minutes=10)
_QUICK_TIMEOUT = timedelta(seconds=30)
_DEFAULT_RETRY = RetryPolicy(maximum_attempts=3)


@dataclass(frozen=True, slots=True)
class ScheduledPublishWorkflowInput:
    project_id: str
    video_id: str
    publish_at_iso: str
    requested_by_user_id: str


@dataclass(frozen=True, slots=True)
class ScheduledPublishWorkflowOutput:
    ok: bool
    error: str | None = None


@workflow.defn(name="ScheduledPublishWorkflow")
class ScheduledPublishWorkflow:
    """ARCHITECTURE.md §5.1's "Schedule / Publish (child workflow, timer)"
    stage — a standalone, independently-invocable workflow (not yet wired
    as an automatic child of `VideoProductionWorkflow`, which currently
    publishes immediately inline; scheduling integration is a follow-up).
    Waits until `publish_at_iso`, then runs the `publisher` agent — which,
    same as `VideoProductionWorkflow`'s inline publish step, currently
    always fails with the honest Phase-8 `NotImplementedError` since no
    real YouTube upload exists yet."""

    @workflow.run
    async def run(self, data: ScheduledPublishWorkflowInput) -> ScheduledPublishWorkflowOutput:
        info = workflow.info()
        job: RecordJobStartedActivityOutput = await workflow.execute_activity(
            "record_job_started",
            RecordJobStartedActivityInput(
                workflow_id=info.workflow_id,
                run_id=info.run_id,
                workflow_type="ScheduledPublishWorkflow",
                project_id=data.project_id,
            ),
            start_to_close_timeout=_QUICK_TIMEOUT,
            result_type=RecordJobStartedActivityOutput,
        )
        job_id = job.job_id

        try:
            publish_at = datetime.fromisoformat(data.publish_at_iso)
            if publish_at.tzinfo is None:
                publish_at = publish_at.replace(tzinfo=UTC)
            delay = publish_at - workflow.now()
            if delay > timedelta(0):
                await workflow.sleep(delay)

            result: RunAgentOutput = await workflow.execute_activity(
                "run_agent",
                RunAgentInput(agent_name="publisher", project_id=data.project_id, payload={"video_id": data.video_id}),
                start_to_close_timeout=_AGENT_STEP_TIMEOUT,
                retry_policy=_DEFAULT_RETRY,
                result_type=RunAgentOutput,
            )
            if not result.ok:
                raise ApplicationError(f"publisher agent failed: {result.error}")

            await workflow.execute_activity(
                "update_job_status",
                UpdateJobStatusActivityInput(job_id=job_id, status="completed"),
                start_to_close_timeout=_QUICK_TIMEOUT,
            )
            return ScheduledPublishWorkflowOutput(ok=True)

        except Exception as exc:
            await workflow.execute_activity(
                "update_job_status",
                UpdateJobStatusActivityInput(job_id=job_id, status="failed", error=str(exc)),
                start_to_close_timeout=_QUICK_TIMEOUT,
            )
            return ScheduledPublishWorkflowOutput(ok=False, error=str(exc))
