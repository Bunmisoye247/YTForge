from __future__ import annotations

import json
import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.use_cases.seo import SetSeoMetadataInput, set_seo_metadata
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import parse_json_response, run_llm_step


class SEOAgent:
    """Consumes script + video, produces title/description/tags/chapters
    (ARCHITECTURE.md §3). `task.payload["video_id"]` is required."""

    name = "seo"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        video_id_raw = task.payload.get("video_id")
        if not video_id_raw:
            return AgentResult.failure("seo agent requires payload['video_id']")

        video = await ctx.uow.videos.get_by_id(uuid.UUID(video_id_raw))
        if video is None:
            raise NotFoundError("Video", video_id_raw)

        script = await ctx.uow.scripts.get_latest_for_project(task.project_id)
        script_summary = json.dumps(script.sections) if script else ""

        _rendered, response = await run_llm_step(
            ctx,
            agent="seo",
            template_name="metadata",
            route_name="seo",
            variables={"video_title": video.title, "video_description": video.description, "script_summary": script_summary},
            project_id=task.project_id,
        )

        try:
            parsed = parse_json_response(response.content)
        except json.JSONDecodeError:
            return AgentResult.failure(f"seo agent did not return valid JSON: {response.content[:200]!r}")

        seo = await set_seo_metadata(
            ctx.uow,
            SetSeoMetadataInput(
                video_id=video.id,
                title=parsed.get("title", video.title)[:100],
                description=parsed.get("description", video.description)[:5000],
                tags=parsed.get("tags", []),
                chapters=parsed.get("chapters", []),
                keywords=parsed.get("keywords", []),
            ),
        )
        return AgentResult.success(seo_metadata_id=str(seo.id))
