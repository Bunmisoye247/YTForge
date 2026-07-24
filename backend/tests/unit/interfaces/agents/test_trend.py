from __future__ import annotations

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.pagination import PageParams
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.trend import TrendAgent


async def test_trend_agent_scores_and_records_candidates() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await TrendAgent().run(
        AgentTask(
            project_id=project.id,
            payload={"candidate_topics": ["on-device AI", "quantum computing"]},
        ),
        ctx,
    )

    assert result.ok, result.error
    assert len(result.output["trend_ids"]) == 2
    trends = await uow.trends.list_for_channel(channel.id, PageParams())
    assert trends.total == 2
