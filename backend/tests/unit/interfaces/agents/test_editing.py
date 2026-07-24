from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.assets import RegisterAssetInput, register_asset
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.domain.entities import Scene, Storyboard
from ytforge.domain.enums import AssetType, StoryboardStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.editing import EditingAgent


async def test_editing_agent_gathers_scene_assets_and_renders() -> None:
    """Real orchestration (gathering each scene's asset into an
    EditingRequest) is exercised here; `render()` runs against
    FakeEditingPipeline (Phase 7) — no ffmpeg binary needed for this test,
    only the fake's deterministic output."""
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
        id=uuid7(), storyboard_id=storyboard.id, sequence_index=0, description="Intro",
        duration_seconds=Decimal("8"), created_at=now, updated_at=now,
    )
    await uow.scenes.add(scene)
    await register_asset(
        uow,
        RegisterAssetInput(
            project_id=project.id, scene_id=scene.id, asset_type=AssetType.CLIP,
            bucket="raw-assets", object_key="clip.mp4",
        ),
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await EditingAgent().run(
        AgentTask(project_id=project.id, payload={"storyboard_id": str(storyboard.id)}), ctx
    )

    assert result.ok, result.error
    assert result.output["render_object_key"].endswith(".mp4")
    assert result.output["render_asset_id"]
