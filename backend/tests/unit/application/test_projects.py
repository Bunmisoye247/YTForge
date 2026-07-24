from __future__ import annotations

import pytest
from uuid6 import uuid7

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import (
    CreateProjectInput,
    create_project,
    transition_project_status,
)
from ytforge.domain.enums import ProjectStatus


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def test_create_project_requires_existing_channel(uow: FakeUnitOfWork) -> None:
    with pytest.raises(NotFoundError):
        await create_project(uow, CreateProjectInput(channel_id=uuid7(), title="Video idea"))


async def test_create_project_starts_as_idea(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="Video idea"))
    assert project.status == ProjectStatus.IDEA


async def test_transition_project_status_emits_event(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="Video idea"))

    updated = await transition_project_status(uow, project.id, ProjectStatus.IN_PROGRESS)

    assert updated.status == ProjectStatus.IN_PROGRESS
    assert any(e["event_type"] == "ProjectStatusChanged" for e in uow.events)


async def test_transition_project_status_rejects_illegal_transition(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="Video idea"))

    with pytest.raises(InvalidStateError):
        await transition_project_status(uow, project.id, ProjectStatus.COMPLETED)
