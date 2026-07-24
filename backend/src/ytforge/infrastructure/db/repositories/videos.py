from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import SeoMetadata, Video
from ytforge.infrastructure.db.models import SeoMetadata as SeoMetadataOrm
from ytforge.infrastructure.db.models import Video as VideoOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _video_to_domain(row: VideoOrm) -> Video:
    return Video(
        id=row.id,
        project_id=row.project_id,
        render_asset_id=row.render_asset_id,
        title=row.title,
        description=row.description,
        status=row.status,
        synthetic_content_disclosure=row.synthetic_content_disclosure,
        youtube_video_id=row.youtube_video_id,
        scheduled_publish_at=row.scheduled_publish_at,
        published_at=row.published_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _seo_to_domain(row: SeoMetadataOrm) -> SeoMetadata:
    return SeoMetadata(
        id=row.id,
        video_id=row.video_id,
        title=row.title,
        description=row.description,
        thumbnail_asset_id=row.thumbnail_asset_id,
        tags=row.tags,
        chapters=row.chapters,
        keywords=row.keywords,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyVideoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, video_id: uuid.UUID) -> Video | None:
        row = await self._session.get(VideoOrm, video_id)
        return _video_to_domain(row) if row is not None else None

    async def add(self, video: Video) -> None:
        row = VideoOrm(
            id=video.id,
            project_id=video.project_id,
            render_asset_id=video.render_asset_id,
            youtube_video_id=video.youtube_video_id,
            title=video.title,
            description=video.description,
            synthetic_content_disclosure=video.synthetic_content_disclosure,
            status=video.status,
            scheduled_publish_at=video.scheduled_publish_at,
            published_at=video.published_at,
            created_at=video.created_at,
            updated_at=video.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, video: Video) -> None:
        row = await self._session.get(VideoOrm, video.id)
        assert row is not None
        row.title = video.title
        row.description = video.description
        row.status = video.status
        row.youtube_video_id = video.youtube_video_id
        row.scheduled_publish_at = video.scheduled_publish_at
        row.published_at = video.published_at
        row.updated_at = video.updated_at
        await self._session.flush()

    async def list_for_project(self, project_id: uuid.UUID, params: PageParams) -> Page[Video]:
        stmt = (
            select(VideoOrm)
            .where(VideoOrm.project_id == project_id)
            .order_by(VideoOrm.created_at.desc())
        )
        return await paginate(self._session, stmt, params, _video_to_domain)


class SqlAlchemySeoMetadataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_video(self, video_id: uuid.UUID) -> SeoMetadata | None:
        row = await self._session.scalar(select(SeoMetadataOrm).where(SeoMetadataOrm.video_id == video_id))
        return _seo_to_domain(row) if row is not None else None

    async def add(self, seo_metadata: SeoMetadata) -> None:
        row = SeoMetadataOrm(
            id=seo_metadata.id,
            video_id=seo_metadata.video_id,
            thumbnail_asset_id=seo_metadata.thumbnail_asset_id,
            title=seo_metadata.title,
            description=seo_metadata.description,
            tags=seo_metadata.tags,
            chapters=seo_metadata.chapters,
            keywords=seo_metadata.keywords,
            created_at=seo_metadata.created_at,
            updated_at=seo_metadata.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, seo_metadata: SeoMetadata) -> None:
        row = await self._session.get(SeoMetadataOrm, seo_metadata.id)
        assert row is not None
        row.thumbnail_asset_id = seo_metadata.thumbnail_asset_id
        row.title = seo_metadata.title
        row.description = seo_metadata.description
        row.tags = seo_metadata.tags
        row.chapters = seo_metadata.chapters
        row.keywords = seo_metadata.keywords
        row.updated_at = seo_metadata.updated_at
        await self._session.flush()
