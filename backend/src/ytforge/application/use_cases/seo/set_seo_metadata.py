from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import SeoMetadata


@dataclass(frozen=True, slots=True)
class SetSeoMetadataInput:
    video_id: uuid.UUID
    title: str
    description: str
    thumbnail_asset_id: uuid.UUID | None = None
    tags: list[Any] = field(default_factory=list)
    chapters: list[Any] = field(default_factory=list)
    keywords: list[Any] = field(default_factory=list)


async def set_seo_metadata(uow: UnitOfWork, data: SetSeoMetadataInput) -> SeoMetadata:
    if await uow.videos.get_by_id(data.video_id) is None:
        raise NotFoundError("Video", data.video_id)

    now = datetime.now(UTC)
    existing = await uow.seo_metadata.get_for_video(data.video_id)
    if existing is None:
        seo = SeoMetadata(
            id=uuid7(),
            video_id=data.video_id,
            title=data.title,
            description=data.description,
            thumbnail_asset_id=data.thumbnail_asset_id,
            tags=data.tags,
            chapters=data.chapters,
            keywords=data.keywords,
            created_at=now,
            updated_at=now,
        )
        await uow.seo_metadata.add(seo)
    else:
        existing.title = data.title
        existing.description = data.description
        existing.thumbnail_asset_id = data.thumbnail_asset_id
        existing.tags = data.tags
        existing.chapters = data.chapters
        existing.keywords = data.keywords
        existing.updated_at = now
        await uow.seo_metadata.update(existing)
        seo = existing

    await uow.commit()
    return seo
