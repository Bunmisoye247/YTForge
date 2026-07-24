from __future__ import annotations

import json
import uuid

from ytforge.application.ports.providers import UnitOfWork
from ytforge.infrastructure.config.settings import get_settings
from ytforge.infrastructure.db.session import get_session_factory
from ytforge.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from ytforge.interfaces.agents import AGENTS, AgentTask
from ytforge.interfaces.agents.factory import build_agent_context


async def run_agent(agent_name: str, project_id: str, payload_json: str) -> None:
    agent = AGENTS.get(agent_name)
    if agent is None:
        print(f"Unknown agent {agent_name!r}. Known agents: {', '.join(sorted(AGENTS))}")
        raise SystemExit(1)

    settings = get_settings()
    uow: UnitOfWork = SqlAlchemyUnitOfWork(get_session_factory())

    async with uow:
        ctx = build_agent_context(settings, uow)
        task = AgentTask(project_id=uuid.UUID(project_id), payload=json.loads(payload_json))
        result = await agent.run(task, ctx)

    if result.ok:
        print(f"[{agent_name}] OK: {json.dumps(result.output)}")
    else:
        print(f"[{agent_name}] FAILED: {result.error}")
        raise SystemExit(1)
