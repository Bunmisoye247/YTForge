from __future__ import annotations

import pytest
from uuid6 import uuid7

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.application.use_cases.scripts import CreateScriptVersionInput, create_script_version


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def test_create_script_version_increments_version(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="Idea"))

    v1 = await create_script_version(
        uow, CreateScriptVersionInput(project_id=project.id, sections={"hook": "a"})
    )
    v2 = await create_script_version(
        uow, CreateScriptVersionInput(project_id=project.id, sections={"hook": "b"})
    )

    assert v1.version == 1
    assert v2.version == 2
    assert v1.sections == {"hook": "a"}
