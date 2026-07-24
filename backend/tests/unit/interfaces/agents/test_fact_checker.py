from __future__ import annotations

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.application.use_cases.scripts import CreateScriptVersionInput, create_script_version
from ytforge.domain.enums import FactCheckVerdict
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.fact_checker import FactCheckerAgent


async def test_fact_checker_agent_records_verdict() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))
    script = await create_script_version(
        uow, CreateScriptVersionInput(project_id=project.id, sections={"hook": "h", "body": ["b"], "cta": "c"})
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await FactCheckerAgent().run(AgentTask(project_id=project.id, payload={}), ctx)

    assert result.ok, result.error
    fact_checks = await uow.fact_checks.list_for_script(script.id)
    assert len(fact_checks) == 1
    assert fact_checks[0].verdict == FactCheckVerdict.PASSED
