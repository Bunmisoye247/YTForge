from __future__ import annotations

from datetime import UTC, date, datetime

from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.analytics import IngestDailyMetricInput, ingest_daily_metric
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.domain.entities import Video
from ytforge.domain.enums import VideoStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.analytics import AnalyticsAgent
from ytforge.interfaces.agents.base import AgentTask


async def test_analytics_agent_embeds_insight() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))

    now = datetime.now(UTC)
    video = Video(
        id=uuid7(), project_id=project.id, render_asset_id=uuid7(), title="Published video",
        description="d", status=VideoStatus.PUBLISHED, created_at=now, updated_at=now,
    )
    await uow.videos.add(video)
    await ingest_daily_metric(
        uow, IngestDailyMetricInput(video_id=video.id, date=date.today(), views=1000)
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await AnalyticsAgent().run(
        AgentTask(project_id=project.id, payload={"video_id": str(video.id)}), ctx
    )

    assert result.ok, result.error
    matches = await ctx.vector_store.query("performance_memory", [0.0] * 8, limit=5)
    assert len(matches) == 1
    assert matches[0].payload["video_id"] == str(video.id)


async def test_analytics_agent_requires_ingested_metrics() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))
    now = datetime.now(UTC)
    video = Video(
        id=uuid7(), project_id=project.id, render_asset_id=uuid7(), title="No metrics yet",
        description="d", status=VideoStatus.PUBLISHED, created_at=now, updated_at=now,
    )
    await uow.videos.add(video)

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await AnalyticsAgent().run(
        AgentTask(project_id=project.id, payload={"video_id": str(video.id)}), ctx
    )

    assert not result.ok
