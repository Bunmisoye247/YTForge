from __future__ import annotations

import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.dto.image import ImageRequest
from ytforge.application.use_cases.assets import (
    RegisterAssetInput,
    mark_asset_ready,
    register_asset,
)
from ytforge.domain.enums import AssetType
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import run_llm_step


class ImageAgent:
    """Consumes scenes, produces image assets in object storage
    (ARCHITECTURE.md §3). `task.payload["scene_ids"]` selects which scenes
    to generate images for. Object storage (MinIO) upload wiring doesn't
    exist yet — the registered asset's `object_key` is whatever the
    provider returned (see the image adapters' `pending-upload/...`
    placeholder convention)."""

    name = "image"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        scene_ids: list[str] = task.payload.get("scene_ids", [])
        if not scene_ids:
            return AgentResult.failure("image agent requires payload['scene_ids']")

        asset_ids = []
        for scene_id_raw in scene_ids:
            scene = await ctx.uow.scenes.get_by_id(uuid.UUID(scene_id_raw))
            if scene is None:
                raise NotFoundError("Scene", scene_id_raw)

            _rendered, response = await run_llm_step(
                ctx,
                agent="image",
                template_name="prompt_composer",
                route_name="script_writing",
                variables={"scene_description": scene.description, "raw_image_prompt": scene.image_prompt or ""},
                project_id=task.project_id,
            )

            images = await ctx.model_router.generate_image(
                "image_generation", ImageRequest(prompt=response.content, model="")
            )
            for image in images:
                asset = await register_asset(
                    ctx.uow,
                    RegisterAssetInput(
                        project_id=task.project_id,
                        scene_id=scene.id,
                        asset_type=AssetType.IMAGE,
                        bucket="raw-assets",
                        object_key=image.object_key,
                        provenance={"model": image.model, "cost_usd": image.cost_usd},
                    ),
                )
                await mark_asset_ready(ctx.uow, asset.id)
                asset_ids.append(str(asset.id))

        return AgentResult.success(asset_ids=asset_ids)
