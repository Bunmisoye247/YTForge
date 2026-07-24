from __future__ import annotations

import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import SeoMetadata


async def get_seo_metadata(uow: UnitOfWork, video_id: uuid.UUID) -> SeoMetadata:
    seo = await uow.seo_metadata.get_for_video(video_id)
    if seo is None:
        raise NotFoundError("SeoMetadata", video_id)
    return seo
