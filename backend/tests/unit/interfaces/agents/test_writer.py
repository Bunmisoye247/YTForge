from __future__ import annotations

import pytest
from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.domain.enums import ScriptStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.writer import WriterAgent


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def test_writer_agent_creates_script_version(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="On-device AI"))

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    task = AgentTask(project_id=project.id, payload={"topic": "on-device AI"})

    result = await WriterAgent().run(task, ctx)

    assert result.ok, result.error
    script = await uow.scripts.get_latest_for_project(project.id)
    assert script is not None
    assert script.status == ScriptStatus.DRAFT
    assert "hook" in script.sections
    assert "body" in script.sections
    assert "cta" in script.sections


async def test_writer_agent_requires_topic(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))
    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))

    result = await WriterAgent().run(AgentTask(project_id=project.id, payload={}), ctx)

    assert not result.ok
    assert "topic" in (result.error or "")
