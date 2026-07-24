from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Project
from ytforge.infrastructure.db.models import Project as ProjectOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: ProjectOrm) -> Project:
    return Project(
        id=row.id,
        channel_id=row.channel_id,
        trend_id=row.trend_id,
        created_by_user_id=row.created_by_user_id,
        title=row.title,
        status=row.status,
        budget_usd=row.budget_usd,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        row = await self._session.get(ProjectOrm, project_id)
        return _to_domain(row) if row is not None else None

    async def add(self, project: Project) -> None:
        row = ProjectOrm(
            id=project.id,
            channel_id=project.channel_id,
            trend_id=project.trend_id,
            created_by_user_id=project.created_by_user_id,
            title=project.title,
            status=project.status,
            budget_usd=project.budget_usd,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, project: Project) -> None:
        row = await self._session.get(ProjectOrm, project.id)
        assert row is not None
        row.title = project.title
        row.status = project.status
        row.budget_usd = project.budget_usd
        row.updated_at = project.updated_at
        await self._session.flush()

    async def list_for_channel(self, channel_id: uuid.UUID, params: PageParams) -> Page[Project]:
        stmt = (
            select(ProjectOrm)
            .where(ProjectOrm.channel_id == channel_id)
            .order_by(ProjectOrm.created_at.desc())
        )
        return await paginate(self._session, stmt, params, _to_domain)
