from __future__ import annotations

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.application.use_cases.scripts import CreateScriptVersionInput, create_script_version
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.storyboard import StoryboardAgent


async def test_storyboard_agent_creates_storyboard_and_scenes() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))
    script = await create_script_version(
        uow, CreateScriptVersionInput(project_id=project.id, sections={"hook": "h", "body": ["b"], "cta": "c"})
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await StoryboardAgent().run(
        AgentTask(project_id=project.id, payload={"script_id": str(script.id)}), ctx
    )

    assert result.ok, result.error
    assert len(result.output["scene_ids"]) == 2
    storyboard = await uow.storyboards.get_by_project(project.id)
    assert storyboard is not None
    scenes = await uow.scenes.list_for_storyboard(storyboard.id)
    assert [s.sequence_index for s in scenes] == [0, 1]
