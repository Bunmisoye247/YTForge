from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import Scene, Storyboard
from ytforge.infrastructure.db.models import Scene as SceneOrm
from ytforge.infrastructure.db.models import Storyboard as StoryboardOrm


def _storyboard_to_domain(row: StoryboardOrm) -> Storyboard:
    return Storyboard(
        id=row.id,
        project_id=row.project_id,
        script_id=row.script_id,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _scene_to_domain(row: SceneOrm) -> Scene:
    return Scene(
        id=row.id,
        storyboard_id=row.storyboard_id,
        sequence_index=row.sequence_index,
        description=row.description,
        duration_seconds=row.duration_seconds,
        image_prompt=row.image_prompt,
        video_prompt=row.video_prompt,
        voice_line=row.voice_line,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyStoryboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, storyboard_id: uuid.UUID) -> Storyboard | None:
        row = await self._session.get(StoryboardOrm, storyboard_id)
        return _storyboard_to_domain(row) if row is not None else None

    async def get_by_project(self, project_id: uuid.UUID) -> Storyboard | None:
        row = await self._session.scalar(
            select(StoryboardOrm).where(StoryboardOrm.project_id == project_id)
        )
        return _storyboard_to_domain(row) if row is not None else None

    async def add(self, storyboard: Storyboard) -> None:
        row = StoryboardOrm(
            id=storyboard.id,
            project_id=storyboard.project_id,
            script_id=storyboard.script_id,
            status=storyboard.status,
            created_at=storyboard.created_at,
            updated_at=storyboard.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, storyboard: Storyboard) -> None:
        row = await self._session.get(StoryboardOrm, storyboard.id)
        assert row is not None
        row.status = storyboard.status
        row.updated_at = storyboard.updated_at
        await self._session.flush()


class SqlAlchemySceneRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, scene_id: uuid.UUID) -> Scene | None:
        row = await self._session.get(SceneOrm, scene_id)
        return _scene_to_domain(row) if row is not None else None

    async def add(self, scene: Scene) -> None:
        row = SceneOrm(
            id=scene.id,
            storyboard_id=scene.storyboard_id,
            sequence_index=scene.sequence_index,
            description=scene.description,
            duration_seconds=scene.duration_seconds,
            image_prompt=scene.image_prompt,
            video_prompt=scene.video_prompt,
            voice_line=scene.voice_line,
            created_at=scene.created_at,
            updated_at=scene.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, scene: Scene) -> None:
        row = await self._session.get(SceneOrm, scene.id)
        assert row is not None
        row.sequence_index = scene.sequence_index
        row.description = scene.description
        row.duration_seconds = scene.duration_seconds
        row.image_prompt = scene.image_prompt
        row.video_prompt = scene.video_prompt
        row.voice_line = scene.voice_line
        row.updated_at = scene.updated_at
        await self._session.flush()

    async def list_for_storyboard(self, storyboard_id: uuid.UUID) -> list[Scene]:
        stmt = (
            select(SceneOrm)
            .where(SceneOrm.storyboard_id == storyboard_id)
            .order_by(SceneOrm.sequence_index)
        )
        rows = await self._session.scalars(stmt)
        return [_scene_to_domain(row) for row in rows]
