from __future__ import annotations

import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.dto.editing import EditingRequest, EditingSceneInput
from ytforge.application.use_cases.assets import (
    RegisterAssetInput,
    mark_asset_ready,
    register_asset,
)
from ytforge.domain.enums import AssetType
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext

_ALL_ASSETS = PageParams(limit=200)


class EditingAgent:
    """Consumes all of a storyboard's scene assets, produces a rendered
    MP4 via the FFmpeg pipeline (ARCHITECTURE.md §3, §5.1), and registers
    it as a RENDER asset — matching every other producing agent — so
    `VideoProductionWorkflow` has an asset id to hand to `create_video`.
    `task.payload["storyboard_id"]` is required."""

    name = "editing"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        storyboard_id_raw = task.payload.get("storyboard_id")
        if not storyboard_id_raw:
            return AgentResult.failure("editing agent requires payload['storyboard_id']")

        storyboard_id = uuid.UUID(storyboard_id_raw)
        scenes = await ctx.uow.scenes.list_for_storyboard(storyboard_id)
        if not scenes:
            raise NotFoundError("Scene", f"for storyboard {storyboard_id}")

        assets_page = await ctx.uow.assets.list_for_project(task.project_id, _ALL_ASSETS)
        assets_by_scene = {a.scene_id: a for a in assets_page.items if a.scene_id is not None}

        voiceovers = await ctx.uow.voiceovers.list_for_project(task.project_id)
        voiceover_asset_by_scene = {}
        voiceover_by_scene = {}
        for voiceover in voiceovers:
            if voiceover.scene_id is None:
                continue
            voiceover_by_scene[voiceover.scene_id] = voiceover
            voiceover_asset = await ctx.uow.assets.get_by_id(voiceover.asset_id)
            if voiceover_asset is not None:
                voiceover_asset_by_scene[voiceover.scene_id] = voiceover_asset

        scene_inputs = []
        for scene in scenes:
            asset = assets_by_scene.get(scene.id)
            if asset is None:
                continue
            voice_asset = voiceover_asset_by_scene.get(scene.id)
            scene_voiceover = voiceover_by_scene.get(scene.id)
            scene_inputs.append(
                EditingSceneInput(
                    scene_id=str(scene.id),
                    sequence_index=scene.sequence_index,
                    visual_object_key=asset.object_key,
                    voice_object_key=voice_asset.object_key if voice_asset is not None else None,
                    duration_seconds=float(scene.duration_seconds),
                    transcript=scene_voiceover.transcript if scene_voiceover is not None else None,
                    word_timestamps=scene_voiceover.word_timestamps if scene_voiceover is not None else [],
                )
            )

        request = EditingRequest(project_id=str(task.project_id), scenes=scene_inputs)
        try:
            result = await ctx.editing_pipeline.render(request)
        except NotImplementedError as exc:
            return AgentResult.failure(str(exc))

        asset = await register_asset(
            ctx.uow,
            RegisterAssetInput(
                project_id=task.project_id,
                asset_type=AssetType.RENDER,
                bucket="renders",
                object_key=result.render_object_key,
                provenance={"duration_seconds": result.duration_seconds},
            ),
        )
        await mark_asset_ready(ctx.uow, asset.id)

        return AgentResult.success(render_object_key=result.render_object_key, render_asset_id=str(asset.id))
