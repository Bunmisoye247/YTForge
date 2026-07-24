from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from ytforge.application.dto.llm import LLMMessage, LLMRequest, LLMResponse
from ytforge.application.dto.prompt import RenderedPrompt
from ytforge.application.use_cases.prompts import RecordPromptRunInput, record_prompt_run
from ytforge.domain.enums import PromptRunStatus
from ytforge.interfaces.agents.context import AgentContext


async def run_llm_step(
    ctx: AgentContext,
    *,
    agent: str,
    template_name: str,
    route_name: str,
    variables: dict[str, Any],
    project_id: uuid.UUID,
) -> tuple[RenderedPrompt, LLMResponse]:
    """Shared by every LLM-backed agent: render the versioned prompt, route
    it through `ModelRouter`, and log the interaction as a `PromptRun` (the
    same table `BudgetMeter` sums against). Returns both so the caller can
    parse `response.content` and cite `rendered.version` in its output."""
    rendered = ctx.prompts.render(agent, template_name, variables)
    # `model` is a placeholder — ModelRouter.complete() always overwrites it
    # with whichever provider/model the route resolves to (primary or a
    # fallback), so what's set here never reaches a real provider call.
    request = LLMRequest(model="", messages=[LLMMessage(role="user", content=rendered.content)])
    response = await ctx.model_router.complete(route_name, request)

    template = await ctx.uow.prompt_templates.get_by_agent_and_name(agent, template_name)
    prompt_version_id = None
    if template is not None:
        version = await ctx.uow.prompt_versions.get_latest(template.id)
        prompt_version_id = version.id if version is not None else None

    if prompt_version_id is not None:
        await record_prompt_run(
            ctx.uow,
            RecordPromptRunInput(
                prompt_version_id=prompt_version_id,
                project_id=project_id,
                input_variables=variables,
                rendered_prompt=rendered.content,
                model_used=response.model,
                status=PromptRunStatus.SUCCEEDED,
                response=response.content,
                latency_ms=response.latency_ms,
                cost_usd=Decimal(str(response.cost_usd)) if response.cost_usd is not None else None,
            ),
        )

    return rendered, response
