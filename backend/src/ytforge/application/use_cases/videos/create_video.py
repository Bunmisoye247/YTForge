from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Video
from ytforge.domain.enums import VideoStatus


@dataclass(frozen=True, slots=True)
class CreateVideoInput:
    project_id: uuid.UUID
    render_asset_id: uuid.UUID
    title: str
    description: str
    synthetic_content_disclosure: bool = True


async def create_video(uow: UnitOfWork, data: CreateVideoInput) -> Video:
    if await uow.projects.get_by_id(data.project_id) is None:
        raise NotFoundError("Project", data.project_id)
    if await uow.assets.get_by_id(data.render_asset_id) is None:
        raise NotFoundError("Asset", data.render_asset_id)

    now = datetime.now(UTC)
    video = Video(
        id=uuid7(),
        project_id=data.project_id,
        render_asset_id=data.render_asset_id,
        title=data.title,
        description=data.description,
        status=VideoStatus.DRAFT,
        synthetic_content_disclosure=data.synthetic_content_disclosure,
        created_at=now,
        updated_at=now,
    )
    await uow.videos.add(video)
    await uow.commit()
    return video
