from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError

from ytforge.interfaces.activity_dto import (
    CheckBudgetActivityInput,
    CheckBudgetActivityOutput,
    CreateVideoActivityInput,
    CreateVideoActivityOutput,
    EmitEventActivityInput,
    OrphanAssetsActivityInput,
    PreflightCheckActivityInput,
    PreflightCheckActivityOutput,
    RecordJobStartedActivityInput,
    RecordJobStartedActivityOutput,
    RequestApprovalActivityInput,
    RequestApprovalActivityOutput,
    RequestPublishApprovalActivityInput,
    RequestPublishApprovalActivityOutput,
    RunAgentInput,
    RunAgentOutput,
    UpdateJobStatusActivityInput,
)

_AGENT_STEP_TIMEOUT = timedelta(minutes=10)
_QUICK_TIMEOUT = timedelta(seconds=30)
_DEFAULT_RETRY = RetryPolicy(maximum_attempts=3)
# Matches `TemporalSettings.renderer_task_queue`'s default. Hardcoded
# rather than read from settings at workflow-run time — workflow code
# must be deterministic across replays, and `get_settings()` reads env
# vars, which a config-driven task queue name would make non-deterministic
# if it ever changed between a workflow's original run and a replay.
_RENDERER_TASK_QUEUE = "ytforge-renderer"


@dataclass(frozen=True, slots=True)
class VideoProductionWorkflowInput:
    project_id: str
    topic: str
    requested_by_user_id: str
    video_title: str = ""
    video_description: str = ""


@dataclass(frozen=True, slots=True)
class VideoProductionWorkflowOutput:
    ok: bool
    video_id: str | None = None
    error: str | None = None


@workflow.defn(name="VideoProductionWorkflow")
class VideoProductionWorkflow:
    """The main pipeline (ARCHITECTURE.md §5.1): Research -> ScriptWrite ->
    FactCheck -> (flagged? HumanReview gate) -> Storyboard -> fan-out
    (Image/Video/Voice) -> Editing -> SEO -> APPROVAL GATE (publish) ->
    Upload. TrendDiscovery isn't a step here — it's the standalone
    `TrendDiscoveryCronWorkflow`; this workflow starts from an
    already-selected project/topic. There's no dedicated Thumbnail agent
    among Phase 6's 12 (thumbnails aren't a distinct agent), so that
    diagram box is not separately modeled — flagged here rather than
    silently dropped."""

    def __init__(self) -> None:
        self._decisions: dict[str, str] = {}
        self._created_asset_ids: list[str] = []
        self._pending_approval_id: str | None = None

    @workflow.signal(name="approval_decided")
    def approval_decided(self, approval_id: str, status: str) -> None:
        self._decisions[approval_id] = status

    @workflow.query(name="pending_approval_id")
    def pending_approval_id(self) -> str | None:
        """Lets a caller (dashboard, or a test) discover which approval
        this run is currently blocked on without needing to separately
        query the `approvals` table."""
        return self._pending_approval_id

    async def _run_agent(
        self, agent_name: str, project_id: str, payload: dict[str, Any], *, task_queue: str | None = None
    ) -> RunAgentOutput:
        result: RunAgentOutput = await workflow.execute_activity(
            "run_agent",
            RunAgentInput(agent_name=agent_name, project_id=project_id, payload=payload),
            start_to_close_timeout=_AGENT_STEP_TIMEOUT,
            retry_policy=_DEFAULT_RETRY,
            result_type=RunAgentOutput,
            task_queue=task_queue,
        )
        if not result.ok:
            raise ApplicationError(f"{agent_name} agent failed: {result.error}")
        return result

    async def _emit(self, event_type: str, project_id: str, payload: dict[str, Any]) -> None:
        await workflow.execute_activity(
            "emit_event",
            EmitEventActivityInput(
                aggregate_type="project", aggregate_id=project_id, event_type=event_type, payload=payload
            ),
            start_to_close_timeout=_QUICK_TIMEOUT,
        )

    async def _wait_for_decision(self, approval_id: str) -> str:
        self._pending_approval_id = approval_id
        await workflow.wait_condition(lambda: approval_id in self._decisions)
        self._pending_approval_id = None
        return self._decisions[approval_id]

    async def _fail(self, job_id: str, message: str) -> VideoProductionWorkflowOutput:
        if self._created_asset_ids:
            await workflow.execute_activity(
                "orphan_assets",
                OrphanAssetsActivityInput(asset_ids=self._created_asset_ids),
                start_to_close_timeout=_QUICK_TIMEOUT,
            )
        await workflow.execute_activity(
            "update_job_status",
            UpdateJobStatusActivityInput(job_id=job_id, status="failed", error=message),
            start_to_close_timeout=_QUICK_TIMEOUT,
        )
        return VideoProductionWorkflowOutput(ok=False, error=message)

    @workflow.run
    async def run(self, data: VideoProductionWorkflowInput) -> VideoProductionWorkflowOutput:
        info = workflow.info()
        job: RecordJobStartedActivityOutput = await workflow.execute_activity(
            "record_job_started",
            RecordJobStartedActivityInput(
                workflow_id=info.workflow_id,
                run_id=info.run_id,
                workflow_type="VideoProductionWorkflow",
                project_id=data.project_id,
            ),
            start_to_close_timeout=_QUICK_TIMEOUT,
            result_type=RecordJobStartedActivityOutput,
        )
        job_id = job.job_id

        try:
            await self._emit("PipelineStageStarted", data.project_id, {"stage": "preflight"})
            preflight: PreflightCheckActivityOutput = await workflow.execute_activity(
                "preflight_check",
                PreflightCheckActivityInput(project_id=data.project_id),
                start_to_close_timeout=_QUICK_TIMEOUT,
                result_type=PreflightCheckActivityOutput,
            )
            if not preflight.ok:
                return await self._fail(job_id, f"preflight check failed: {'; '.join(preflight.errors)}")

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "research"})
            await self._run_agent("research", data.project_id, {"topic": data.topic})

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "script_write"})
            writer = await self._run_agent("writer", data.project_id, {"topic": data.topic})
            script_id = writer.output["script_id"]

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "fact_check"})
            fact_check = await self._run_agent("fact_checker", data.project_id, {"script_id": script_id})

            if fact_check.output.get("verdict") == "flagged":
                await self._emit("PipelineStageStarted", data.project_id, {"stage": "human_review"})
                approval: RequestApprovalActivityOutput = await workflow.execute_activity(
                    "request_approval",
                    RequestApprovalActivityInput(
                        kind="script_review",
                        requested_by_user_id=data.requested_by_user_id,
                        workflow_id=info.workflow_id,
                        payload={"script_id": script_id, "fact_check_id": fact_check.output["fact_check_id"]},
                    ),
                    start_to_close_timeout=_QUICK_TIMEOUT,
                    result_type=RequestApprovalActivityOutput,
                )
                decision = await self._wait_for_decision(approval.approval_id)
                if decision != "approved":
                    return await self._fail(job_id, "script review rejected")

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "storyboard"})
            storyboard = await self._run_agent("storyboard", data.project_id, {"script_id": script_id})
            storyboard_id = storyboard.output["storyboard_id"]
            scene_ids = storyboard.output["scene_ids"]

            budget: CheckBudgetActivityOutput = await workflow.execute_activity(
                "check_budget",
                CheckBudgetActivityInput(project_id=data.project_id),
                start_to_close_timeout=_QUICK_TIMEOUT,
                result_type=CheckBudgetActivityOutput,
            )
            if budget.is_exhausted:
                # ARCHITECTURE.md §5.1's "budget guard" — checked here since
                # the fan-out (image/video/voice generation) is the single
                # most expensive stage. Treated as a terminal failure rather
                # than a full approval-gate pause (which would need a new
                # ApprovalKind + reviewer UI) — a simplification, not a
                # dodge: the operator sees exactly why in `jobs.error` and
                # can raise the budget and re-run.
                return await self._fail(
                    job_id, f"budget exhausted: spent {budget.spent_usd} of {budget.budget_usd}"
                )

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "media_generation"})
            image_result, video_result, voice_result = await asyncio.gather(
                self._run_agent("image", data.project_id, {"scene_ids": scene_ids}),
                self._run_agent("video", data.project_id, {"scene_ids": scene_ids}),
                self._run_agent("voice", data.project_id, {"scene_ids": scene_ids}),
            )
            self._created_asset_ids.extend(image_result.output.get("asset_ids", []))
            self._created_asset_ids.extend(video_result.output.get("asset_ids", []))
            self._created_asset_ids.extend(voice_result.output.get("asset_ids", []))

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "editing"})
            editing = await self._run_agent(
                "editing", data.project_id, {"storyboard_id": storyboard_id}, task_queue=_RENDERER_TASK_QUEUE
            )
            render_asset_id = editing.output["render_asset_id"]
            self._created_asset_ids.append(render_asset_id)

            video: CreateVideoActivityOutput = await workflow.execute_activity(
                "create_video",
                CreateVideoActivityInput(
                    project_id=data.project_id,
                    render_asset_id=render_asset_id,
                    title=data.video_title or data.topic,
                    description=data.video_description or data.topic,
                ),
                start_to_close_timeout=_QUICK_TIMEOUT,
                result_type=CreateVideoActivityOutput,
            )
            video_id = video.video_id

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "seo"})
            await self._run_agent("seo", data.project_id, {"video_id": video_id})

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "publish_approval"})
            publish_approval: RequestPublishApprovalActivityOutput = await workflow.execute_activity(
                "request_publish_approval",
                RequestPublishApprovalActivityInput(
                    video_id=video_id, requested_by_user_id=data.requested_by_user_id, workflow_id=info.workflow_id
                ),
                start_to_close_timeout=_QUICK_TIMEOUT,
                result_type=RequestPublishApprovalActivityOutput,
            )
            decision = await self._wait_for_decision(publish_approval.approval_id)
            if decision != "approved":
                await workflow.execute_activity(
                    "update_job_status",
                    UpdateJobStatusActivityInput(job_id=job_id, status="cancelled"),
                    start_to_close_timeout=_QUICK_TIMEOUT,
                )
                return VideoProductionWorkflowOutput(ok=False, video_id=video_id, error="publish rejected")

            await self._emit("PipelineStageStarted", data.project_id, {"stage": "upload"})
            await self._run_agent("publisher", data.project_id, {"video_id": video_id})

            await workflow.execute_activity(
                "update_job_status",
                UpdateJobStatusActivityInput(job_id=job_id, status="completed"),
                start_to_close_timeout=_QUICK_TIMEOUT,
            )
            return VideoProductionWorkflowOutput(ok=True, video_id=video_id)

        except Exception as exc:
            return await self._fail(job_id, str(exc))
