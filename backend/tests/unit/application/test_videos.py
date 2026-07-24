from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.use_cases.videos import mark_video_uploaded
from ytforge.domain.entities import Video
from ytforge.domain.enums import VideoStatus


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def _draft_video(uow: FakeUnitOfWork, status: VideoStatus = VideoStatus.DRAFT) -> Video:
    now = datetime.now(UTC)
    video = Video(
        id=uuid7(),
        project_id=uuid7(),
        render_asset_id=uuid7(),
        title="T",
        description="D",
        status=status,
        created_at=now,
        updated_at=now,
    )
    await uow.videos.add(video)
    return video


async def test_mark_video_uploaded_transitions_status_and_sets_youtube_id(uow: FakeUnitOfWork) -> None:
    video = await _draft_video(uow)

    updated = await mark_video_uploaded(uow, video.id, "yt-video-123")

    assert updated.status == VideoStatus.UPLOADED
    assert updated.youtube_video_id == "yt-video-123"
    assert any(e["event_type"] == "VideoPublished" for e in uow.events)


async def test_mark_video_uploaded_requires_existing_video(uow: FakeUnitOfWork) -> None:
    with pytest.raises(NotFoundError):
        await mark_video_uploaded(uow, uuid7(), "yt-video-123")


async def test_mark_video_uploaded_rejects_already_published_video(uow: FakeUnitOfWork) -> None:
    video = await _draft_video(uow, status=VideoStatus.PUBLISHED)

    with pytest.raises(InvalidStateError):
        await mark_video_uploaded(uow, video.id, "yt-video-123")
