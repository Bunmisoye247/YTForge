from __future__ import annotations

import uuid

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.dto.youtube import YouTubeUploadRequest
from ytforge.application.use_cases.quota import (
    RecordQuotaUsageInput,
    check_quota_budget,
    record_quota_usage,
)
from ytforge.application.use_cases.videos import mark_video_uploaded
from ytforge.domain.enums import ApprovalKind, ApprovalStatus
from ytforge.infrastructure.telemetry.pipeline_metrics import quota_remaining
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext


class PublisherAgent:
    """Consumes a granted PUBLISH approval, produces an uploaded video
    (ARCHITECTURE.md §3, and the hard rule: publishing is approval-gated).
    `task.payload["video_id"]` is required. Real YouTube upload (Phase 8):
    checks `api_quota_ledger` before spending more quota, uploads via
    `YouTubeGateway`, then transitions the video to UPLOADED and records
    the quota spend — all three only happen together, never partially."""

    name = "publisher"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        video_id_raw = task.payload.get("video_id")
        if not video_id_raw:
            return AgentResult.failure("publisher agent requires payload['video_id']")
        video_id = uuid.UUID(video_id_raw)

        video = await ctx.uow.videos.get_by_id(video_id)
        if video is None:
            raise NotFoundError("Video", video_id_raw)

        approved_page = await ctx.uow.approvals.list_by_status(ApprovalStatus.APPROVED, PageParams(limit=200))
        has_publish_approval = any(
            a.kind == ApprovalKind.PUBLISH and a.payload.get("video_id") == str(video_id)
            for a in approved_page.items
        )
        if not has_publish_approval:
            raise ConflictError(f"video {video_id} has no granted PUBLISH approval")

        project = await ctx.uow.projects.get_by_id(task.project_id)
        if project is None:
            raise NotFoundError("Project", task.project_id)

        channel = await ctx.uow.channels.get_by_id(project.channel_id)
        if channel is None:
            raise NotFoundError("Channel", project.channel_id)

        budget = await check_quota_budget(ctx.uow, channel.id, ctx.youtube_daily_quota_budget)
        quota_remaining.set(budget.units_remaining, {"channel_id": str(channel.id)})
        if budget.units_remaining < ctx.youtube_upload_quota_cost:
            return AgentResult.failure(
                f"YouTube API quota for channel {channel.id} would be exhausted by this upload "
                f"({budget.units_remaining} units remaining, upload costs {ctx.youtube_upload_quota_cost})"
            )

        render_asset = await ctx.uow.assets.get_by_id(video.render_asset_id)
        if render_asset is None:
            raise NotFoundError("Asset", video.render_asset_id)

        request = YouTubeUploadRequest(
            channel_id=str(project.channel_id),
            render_object_key=render_asset.object_key,
            title=video.title,
            description=video.description,
            synthetic_content_disclosure=video.synthetic_content_disclosure,
            refresh_token=channel.oauth_refresh_token or "",
        )
        try:
            result = await ctx.youtube_gateway.upload_video(request)
        except NotImplementedError as exc:
            return AgentResult.failure(str(exc))

        await mark_video_uploaded(ctx.uow, video_id, result.youtube_video_id)
        await record_quota_usage(
            ctx.uow,
            RecordQuotaUsageInput(
                channel_id=channel.id,
                operation="videos.insert",
                units_consumed=result.quota_units_consumed,
                units_budget=ctx.youtube_daily_quota_budget,
            ),
        )
        quota_remaining.set(
            budget.units_remaining - result.quota_units_consumed, {"channel_id": str(channel.id)}
        )

        return AgentResult.success(youtube_video_id=result.youtube_video_id)
