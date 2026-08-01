from __future__ import annotations

import json
from typing import Any

from ytforge.application.common.errors import NotFoundError
from ytforge.application.use_cases.trends import RecordTrendInput, record_trend
from ytforge.domain.enums import TrendSource
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import parse_json_response, run_llm_step


class TrendAgent:
    """Real trend-source fetchers (Google Trends, YT Trending, Reddit, HN,
    X, RSS, News APIs — ARCHITECTURE.md §3) aren't built; this agent scores
    and ranks a candidate list the caller already gathered
    (`task.payload["candidate_topics"]`) via the LLM, then persists the
    ranked results. Swapping in real source fetchers later only changes
    where `candidate_topics` comes from, not this agent's shape."""

    name = "trend"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        candidates: list[str] = task.payload.get("candidate_topics", [])
        if not candidates:
            return AgentResult.failure("trend agent requires payload['candidate_topics']")

        project = await ctx.uow.projects.get_by_id(task.project_id)
        if project is None:
            raise NotFoundError("Project", task.project_id)

        _rendered, response = await run_llm_step(
            ctx,
            agent="trend",
            template_name="scoring",
            route_name="trend_scoring",
            variables={"candidate_topics": candidates},
            project_id=task.project_id,
        )

        try:
            scored: list[dict[str, Any]] = parse_json_response(response.content)
        except json.JSONDecodeError:
            return AgentResult.failure(f"trend agent did not return valid JSON: {response.content[:200]!r}")

        trend_ids = []
        for entry in scored:
            trend = await record_trend(
                ctx.uow,
                RecordTrendInput(
                    channel_id=project.channel_id,
                    source=TrendSource.RSS,
                    topic=str(entry["topic"]),
                    score=float(entry.get("score", 0.0)),
                    raw_payload={"rationale": entry.get("rationale", "")},
                ),
            )
            trend_ids.append(str(trend.id))

        return AgentResult.success(trend_ids=trend_ids)
