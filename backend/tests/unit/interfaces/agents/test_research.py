from __future__ import annotations

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.pagination import PageParams
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.research import ResearchAgent


async def test_research_agent_creates_document_and_embeds_it() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await ResearchAgent().run(
        AgentTask(project_id=project.id, payload={"topic": "on-device AI"}), ctx
    )

    assert result.ok, result.error
    docs = await uow.research_documents.list_for_project(project.id, PageParams())
    assert docs.total == 1

    matches = await ctx.vector_store.query("research", [0.0] * 8, limit=5)
    assert len(matches) == 1
    assert matches[0].payload["project_id"] == str(project.id)
