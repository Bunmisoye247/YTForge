from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Video
from ytforge.domain.enums import VideoStatus


@dataclass(frozen=True, slots=True)
class UpdateVideoInput:
    title: str | None = None
    description: str | None = None


async def update_video(uow: UnitOfWork, video_id: uuid.UUID, data: UpdateVideoInput) -> Video:
    video = await uow.videos.get_by_id(video_id)
    if video is None:
        raise NotFoundError("Video", video_id)
    if video.status != VideoStatus.DRAFT:
        raise ConflictError("only draft videos can be edited")

    if data.title is not None:
        video.title = data.title
    if data.description is not None:
        video.description = data.description
    video.updated_at = datetime.now(UTC)

    await uow.videos.update(video)
    await uow.commit()
    return video
