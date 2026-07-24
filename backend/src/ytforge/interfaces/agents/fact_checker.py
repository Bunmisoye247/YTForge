from __future__ import annotations

import json
import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.use_cases.fact_check import RecordFactCheckInput, record_fact_check
from ytforge.domain.enums import FactCheckVerdict
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import run_llm_step


class FactCheckerAgent:
    """Consumes a script, produces a verdict + flags (ARCHITECTURE.md §3).
    `task.payload["script_id"]` selects which script version; falls back
    to the project's latest version if omitted."""

    name = "fact_checker"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        script_id_raw = task.payload.get("script_id")
        if script_id_raw:
            script = await ctx.uow.scripts.get_by_id(uuid.UUID(script_id_raw))
        else:
            script = await ctx.uow.scripts.get_latest_for_project(task.project_id)
        if script is None:
            raise NotFoundError("Script", script_id_raw or task.project_id)

        _rendered, response = await run_llm_step(
            ctx,
            agent="fact_checker",
            template_name="verify_claims",
            route_name="fact_checking",
            variables={"script_sections": json.dumps(script.sections)},
            project_id=task.project_id,
        )

        try:
            parsed = json.loads(response.content)
            verdict = FactCheckVerdict(parsed["verdict"])
            flags = parsed.get("flags", [])
        except (json.JSONDecodeError, KeyError, ValueError):
            return AgentResult.failure(
                f"fact_checker agent did not return valid output: {response.content[:200]!r}"
            )

        fact_check = await record_fact_check(
            ctx.uow,
            RecordFactCheckInput(
                script_id=script.id, verdict=verdict, flags=flags, model_used=response.model
            ),
        )
        return AgentResult.success(fact_check_id=str(fact_check.id), verdict=verdict.value)
