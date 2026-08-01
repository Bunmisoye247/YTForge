from __future__ import annotations

import json

from ytforge.application.common.pagination import PageParams
from ytforge.application.use_cases.scripts import CreateScriptVersionInput, create_script_version
from ytforge.interfaces.agents.base import AgentResult, AgentTask
from ytforge.interfaces.agents.context import AgentContext
from ytforge.interfaces.agents.support import parse_json_response, run_llm_step


class WriterAgent:
    """Consumes research context, produces a structured script draft
    (ARCHITECTURE.md §3). `task.payload["topic"]` is required; research
    documents already attached to the project are pulled in automatically."""

    name = "writer"

    async def run(self, task: AgentTask, ctx: AgentContext) -> AgentResult:
        topic = task.payload.get("topic")
        if not topic:
            return AgentResult.failure("writer agent requires payload['topic']")

        research_page = await ctx.uow.research_documents.list_for_project(
            task.project_id, PageParams(limit=10)
        )
        research_context = "\n\n".join(
            f"{doc.title}: {doc.content}" for doc in research_page.items
        )

        _rendered, response = await run_llm_step(
            ctx,
            agent="writer",
            template_name="video_script",
            route_name="script_writing",
            variables={"topic": topic, "research_context": research_context},
            project_id=task.project_id,
        )

        try:
            sections = parse_json_response(response.content)
        except json.JSONDecodeError:
            return AgentResult.failure(f"writer agent did not return valid JSON: {response.content[:200]!r}")

        script = await create_script_version(
            ctx.uow,
            CreateScriptVersionInput(
                project_id=task.project_id,
                sections=sections,
                model_used=response.model,
                token_count=response.input_tokens + response.output_tokens,
            ),
        )
        return AgentResult.success(script_id=str(script.id), version=script.version)
