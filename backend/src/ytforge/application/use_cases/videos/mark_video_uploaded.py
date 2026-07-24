from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Video
from ytforge.domain.enums import VideoStatus
from ytforge.domain.errors import InvalidTransitionError


async def mark_video_uploaded(uow: UnitOfWork, video_id: uuid.UUID, youtube_video_id: str) -> Video:
    """Transitions DRAFT -> UPLOADED and records the YouTube video id —
    the only path that does this is a successful `YouTubeGateway.upload_
    video()` call (Video.transition_to's own docstring: "only ever driven
    by Phase-8 code"). Emits `VideoPublished` matching the event name
    ARCHITECTURE.md §3's agent-events table documents for PublisherAgent's
    output, even though the domain status is technically "uploaded" (a
    later scheduled-publish step, not built here, would flip it to
    PUBLISHED once YouTube's own `publishAt` timer fires)."""
    video = await uow.videos.get_by_id(video_id)
    if video is None:
        raise NotFoundError("Video", video_id)

    try:
        video.transition_to(VideoStatus.UPLOADED)
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    video.youtube_video_id = youtube_video_id
    video.updated_at = datetime.now(UTC)

    await uow.videos.update(video)
    await uow.add_event(
        aggregate_type="video",
        aggregate_id=video.id,
        event_type="VideoPublished",
        payload={"youtube_video_id": youtube_video_id},
    )
    await uow.commit()
    return video
