from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from fixtures.agent_context import PROMPTS_DIR, make_test_agent_context
from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.errors import ConflictError
from ytforge.application.use_cases.approvals import DecideApprovalInput, decide_approval
from ytforge.application.use_cases.assets import RegisterAssetInput, register_asset
from ytforge.application.use_cases.channels import CreateChannelInput, create_channel
from ytforge.application.use_cases.projects import CreateProjectInput, create_project
from ytforge.application.use_cases.quota import RecordQuotaUsageInput, record_quota_usage
from ytforge.application.use_cases.videos import request_publish_approval
from ytforge.domain.entities import Video
from ytforge.domain.enums import ApprovalStatus, AssetType, VideoStatus
from ytforge.infrastructure.prompts.jinja_store import FilesystemPromptStore
from ytforge.interfaces.agents.base import AgentTask
from ytforge.interfaces.agents.publisher import PublisherAgent


async def _make_video(uow: FakeUnitOfWork, project_id):  # type: ignore[no-untyped-def]
    asset = await register_asset(
        uow,
        RegisterAssetInput(
            project_id=project_id, asset_type=AssetType.RENDER, bucket="renders", object_key="final.mp4"
        ),
    )
    now = datetime.now(UTC)
    video = Video(
        id=uuid7(), project_id=project_id, render_asset_id=asset.id, title="T", description="D",
        status=VideoStatus.DRAFT, created_at=now, updated_at=now,
    )
    await uow.videos.add(video)
    return video


async def test_publisher_agent_requires_granted_approval() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))
    video = await _make_video(uow, project.id)

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    with pytest.raises(ConflictError):
        await PublisherAgent().run(AgentTask(project_id=project.id, payload={"video_id": str(video.id)}), ctx)


async def test_publisher_agent_uploads_once_approved() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))
    video = await _make_video(uow, project.id)

    approval = await request_publish_approval(uow, video.id, uuid7())
    await decide_approval(
        uow, approval.id, DecideApprovalInput(status=ApprovalStatus.APPROVED, decided_by_user_id=uuid7())
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await PublisherAgent().run(
        AgentTask(project_id=project.id, payload={"video_id": str(video.id)}), ctx
    )

    assert result.ok, result.error
    assert result.output["youtube_video_id"]

    updated_video = await uow.videos.get_by_id(video.id)
    assert updated_video is not None
    assert updated_video.status == VideoStatus.UPLOADED
    assert updated_video.youtube_video_id == result.output["youtube_video_id"]

    ledger_entries = await uow.api_quota_ledger.list_for_channel(
        channel.id, datetime.now(UTC).date(), datetime.now(UTC).date()
    )
    assert len(ledger_entries) == 1
    assert ledger_entries[0].units_consumed == 1600


async def test_publisher_agent_fails_when_quota_would_be_exhausted() -> None:
    uow = FakeUnitOfWork()
    channel = await create_channel(uow, CreateChannelInput(name="C", owner_user_id=uuid7()))
    project = await create_project(uow, CreateProjectInput(channel_id=channel.id, title="X"))
    video = await _make_video(uow, project.id)

    approval = await request_publish_approval(uow, video.id, uuid7())
    await decide_approval(
        uow, approval.id, DecideApprovalInput(status=ApprovalStatus.APPROVED, decided_by_user_id=uuid7())
    )
    await record_quota_usage(
        uow,
        RecordQuotaUsageInput(channel_id=channel.id, operation="videos.insert", units_consumed=9000, units_budget=10000),
    )

    ctx = make_test_agent_context(uow, FilesystemPromptStore(PROMPTS_DIR))
    result = await PublisherAgent().run(
        AgentTask(project_id=project.id, payload={"video_id": str(video.id)}), ctx
    )

    assert not result.ok
    assert "quota" in (result.error or "").lower()
    updated_video = await uow.videos.get_by_id(video.id)
    assert updated_video is not None
    assert updated_video.status == VideoStatus.DRAFT
