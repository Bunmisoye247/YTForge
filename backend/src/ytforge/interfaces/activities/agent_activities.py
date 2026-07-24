from __future__ import annotations

import uuid

from temporalio import activity

from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from ytforge.interfaces.activity_dto import RunAgentInput, RunAgentOutput
from ytforge.interfaces.agents import AGENTS, AgentTask
from ytforge.interfaces.agents.factory import build_agent_context


@activity.defn(name="run_agent")
async def run_agent_activity(data: RunAgentInput) -> RunAgentOutput:
    """Single parameterized activity for all 12 agents rather than 12
    near-identical activity functions — each `workflow.execute_activity`
    call site still gets its own `start_to_close_timeout`/`retry_policy`
    (ARCHITECTURE.md §5.1's "tailored retry policy and timeouts per
    stage"), just via the call-site config rather than 12 separate
    `@activity.defn`s."""
    agent = AGENTS[data.agent_name]
    settings = get_settings()
    uow = SqlAlchemyUnitOfWork(get_session_factory())

    async with uow:
        ctx = build_agent_context(settings, uow)
        task = AgentTask(project_id=uuid.UUID(data.project_id), payload=data.payload)
        result = await agent.run(task, ctx)

    return RunAgentOutput(ok=result.ok, output=result.output, error=result.error)
