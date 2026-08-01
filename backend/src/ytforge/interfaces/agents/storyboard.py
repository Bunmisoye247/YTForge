from __future__ import annotations

import json
import uuid
from decimal import Decimal

from ytforge.application.common.errors import NotFoundError
from ytforge.application.use_cases.storyboard import AddSceneInput, add_scene, create_storyboard
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import parse_json_response, run_llm_step


class StoryboardAgent:
    """Consumes an approved script, produces a scene list
    (ARCHITECTURE.md §3). `task.payload["script_id"]` selects the script."""

    name = "storyboard"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        script_id_raw = task.payload.get("script_id")
        if not script_id_raw:
            return AgentResult.failure("storyboard agent requires payload['script_id']")

        script = await ctx.uow.scripts.get_by_id(uuid.UUID(script_id_raw))
        if script is None:
            raise NotFoundError("Script", script_id_raw)

        _rendered, response = await run_llm_step(
            ctx,
            agent="storyboard",
            template_name="scene_breakdown",
            route_name="storyboard",
            variables={"script_sections": json.dumps(script.sections)},
            project_id=task.project_id,
        )

        try:
            scenes_data: list[dict[str, object]] = parse_json_response(response.content)
        except json.JSONDecodeError:
            return AgentResult.failure(
                f"storyboard agent did not return valid JSON: {response.content[:200]!r}"
            )

        storyboard = await create_storyboard(ctx.uow, task.project_id, script.id)
        scene_ids = []
        for index, scene_data in enumerate(scenes_data):
            scene = await add_scene(
                ctx.uow,
                AddSceneInput(
                    storyboard_id=storyboard.id,
                    sequence_index=index,
                    description=str(scene_data["description"]),
                    duration_seconds=Decimal(str(scene_data.get("duration_seconds", 8))),
                    image_prompt=scene_data.get("image_prompt"),  # type: ignore[arg-type]
                    video_prompt=scene_data.get("video_prompt"),  # type: ignore[arg-type]
                    voice_line=scene_data.get("voice_line"),  # type: ignore[arg-type]
                ),
            )
            scene_ids.append(str(scene.id))

        return AgentResult.success(storyboard_id=str(storyboard.id), scene_ids=scene_ids)
