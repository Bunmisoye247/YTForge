from __future__ import annotations

from datetime import UTC, datetime

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.domain.entities import Video
from ytforge.domain.enums import VideoStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.seo import SEOAgent


async def test_seo_agent_sets_metadata() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    now = datetime.now(UTC)
    video = Video(
        id=uuid7(), project_id=project.id, render_asset_id=uuid7(), title="Draft title",
        description="Draft description", status=VideoStatus.DRAFT, created_at=now, updated_at=now,
    )
    await uow.videos.add(video)

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await SEOAgent().run(
        AgentTask(project_id=project.id, payload={"video_id": str(video.id)}), ctx
    )

    assert result.ok, result.error
    seo = await uow.seo_metadata.get_for_video(video.id)
    assert seo is not None
    assert seo.title == "Optimized Title"
    assert seo.keywords == ["ai", "on-device"]
