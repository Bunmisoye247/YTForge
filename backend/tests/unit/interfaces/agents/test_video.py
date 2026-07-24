from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.pagination import PageParams
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.domain.entities import Scene, Storyboard
from ytforge.domain.enums import AssetStatus, AssetType, StoryboardStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.video import VideoAgent


async def test_video_agent_registers_and_readies_clip_asset() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    now = datetime.now(UTC)
    storyboard = Storyboard(
        id=uuid7(), project_id=project.id, script_id=uuid7(), status=StoryboardStatus.READY,
        created_at=now, updated_at=now,
    )
    await uow.storyboards.add(storyboard)
    scene = Scene(
        id=uuid7(), storyboard_id=storyboard.id, sequence_index=0, description="A phone screen",
        duration_seconds=Decimal("8"), video_prompt="slow push-in", created_at=now, updated_at=now,
    )
    await uow.scenes.add(scene)

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await VideoAgent().run(
        AgentTask(project_id=project.id, payload={"scene_ids": [str(scene.id)]}), ctx
    )

    assert result.ok, result.error
    assets = await uow.assets.list_for_project(project.id, PageParams())
    assert assets.total == 1
    assert assets.items[0].asset_type == AssetType.CLIP
    assert assets.items[0].status == AssetStatus.READY
    assert assets.items[0].object_key.startswith("fake/video/")
