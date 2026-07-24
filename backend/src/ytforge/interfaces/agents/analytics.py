from __future__ import annotations

import uuid

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.dto.vector import VectorPoint
from ytforge.application.use_cases.analytics import get_video_analytics
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import run_llm_step

_QDRANT_COLLECTION = "performance_memory"


class AnalyticsAgent:
    """Consumes ingested metrics for a video, produces a "what worked"
    summary embedded into the `performance_memory` Qdrant collection
    (ARCHITECTURE.md §3) — WriterAgent/SEOAgent retrieve from it later,
    closing the learning-loop requirement. `task.payload["video_id"]`
    is required."""

    name = "analytics"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        video_id_raw = task.payload.get("video_id")
        if not video_id_raw:
            return AgentResult.failure("analytics agent requires payload['video_id']")
        video_id = uuid.UUID(video_id_raw)

        video = await ctx.uow.videos.get_by_id(video_id)
        if video is None:
            raise NotFoundError("Video", video_id_raw)

        analytics = await get_video_analytics(ctx.uow, video_id)
        if not analytics.daily_metrics:
            return AgentResult.failure("no analytics ingested yet for this video")

        metrics_summary = "\n".join(
            f"{m.date}: views={m.views} watch_time_min={m.watch_time_minutes} "
            f"likes={m.likes} subscribers_gained={m.subscribers_gained}"
            for m in analytics.daily_metrics
        )
        retention_summary = "\n".join(
            f"{p.elapsed_video_percent}% elapsed -> {p.audience_retention_percent}% retained"
            for p in analytics.retention_points
        )

        _rendered, response = await run_llm_step(
            ctx,
            agent="analytics",
            template_name="insights",
            route_name="analytics_insights",
            variables={
                "video_title": video.title,
                "metrics_summary": metrics_summary,
                "retention_summary": retention_summary,
            },
            project_id=task.project_id,
        )

        vectors = await ctx.model_router.embed("embeddings", [response.content])
        point_id = str(uuid7())
        await ctx.vector_store.upsert(
            _QDRANT_COLLECTION,
            [
                VectorPoint(
                    id=point_id,
                    vector=vectors[0],
                    payload={
                        "video_id": str(video_id),
                        "project_id": str(task.project_id),
                        "insight": response.content,
                    },
                )
            ],
        )
        return AgentResult.success(insight_point_id=point_id)
