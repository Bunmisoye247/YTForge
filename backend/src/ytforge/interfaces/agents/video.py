from __future__ import annotations

import asyncio
import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.dto.video import VideoJob, VideoJobState, VideoJobStatus, VideoRequest
from ytforge.application.use_cases.assets import (
    RegisterAssetInput,
    mark_asset_failed,
    mark_asset_ready,
    register_asset,
)
from ytforge.domain.enums import AssetType
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import run_llm_step

_POLL_INTERVAL_S = 2.0
_POLL_ATTEMPTS = 60


class VideoAgent:
    """Consumes scenes, produces video clip assets (ARCHITECTURE.md §3).
    `task.payload["scene_ids"]` selects which scenes to generate clips
    for. Video generation is an async job — polls until terminal."""

    name = "video"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        scene_ids: list[str] = task.payload.get("scene_ids", [])
        if not scene_ids:
            return AgentResult.failure("video agent requires payload['scene_ids']")

        asset_ids = []
        for scene_id_raw in scene_ids:
            scene = await ctx.uow.scenes.get_by_id(uuid.UUID(scene_id_raw))
            if scene is None:
                raise NotFoundError("Scene", scene_id_raw)

            _rendered, response = await run_llm_step(
                ctx,
                agent="video_gen",
                template_name="prompt_composer",
                route_name="script_writing",
                variables={"scene_description": scene.description, "raw_video_prompt": scene.video_prompt or ""},
                project_id=task.project_id,
            )

            job = await ctx.model_router.generate_video(
                "video_generation",
                VideoRequest(prompt=response.content, model="", duration_seconds=float(scene.duration_seconds)),
            )

            asset = await register_asset(
                ctx.uow,
                RegisterAssetInput(
                    project_id=task.project_id,
                    scene_id=scene.id,
                    asset_type=AssetType.CLIP,
                    bucket="raw-assets",
                    object_key=f"pending/{job.provider}/{job.provider_job_id}",
                    provenance={"provider": job.provider, "provider_job_id": job.provider_job_id},
                ),
            )

            status = await self._await_completion(ctx, job)
            if status.state == VideoJobState.COMPLETED and status.object_key:
                asset.object_key = status.object_key
                await ctx.uow.assets.update(asset)
                await mark_asset_ready(ctx.uow, asset.id)
            else:
                await mark_asset_failed(ctx.uow, asset.id)

            asset_ids.append(str(asset.id))

        return AgentResult.success(asset_ids=asset_ids)

    async def _await_completion(self, ctx: AgentContext, job: VideoJob) -> VideoJobStatus:
        for _ in range(_POLL_ATTEMPTS):
            status = await ctx.model_router.poll_video("video_generation", job)
            if status.state in (VideoJobState.COMPLETED, VideoJobState.FAILED):
                return status
            await asyncio.sleep(_POLL_INTERVAL_S)
        return await ctx.model_router.poll_video("video_generation", job)
