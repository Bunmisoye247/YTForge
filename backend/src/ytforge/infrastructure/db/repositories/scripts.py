from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Script
from ytforge.infrastructure.db.models import Script as ScriptOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: ScriptOrm) -> Script:
    return Script(
        id=row.id,
        project_id=row.project_id,
        version=row.version,
        status=row.status,
        sections=row.sections,
        model_used=row.model_used,
        token_count=row.token_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyScriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, script_id: uuid.UUID) -> Script | None:
        row = await self._session.get(ScriptOrm, script_id)
        return _to_domain(row) if row is not None else None

    async def add(self, script: Script) -> None:
        row = ScriptOrm(
            id=script.id,
            project_id=script.project_id,
            version=script.version,
            status=script.status,
            sections=script.sections,
            model_used=script.model_used,
            token_count=script.token_count,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, script: Script) -> None:
        row = await self._session.get(ScriptOrm, script.id)
        assert row is not None
        row.status = script.status
        row.sections = script.sections
        row.model_used = script.model_used
        row.token_count = script.token_count
        row.updated_at = script.updated_at
        await self._session.flush()

    async def get_latest_for_project(self, project_id: uuid.UUID) -> Script | None:
        stmt = (
            select(ScriptOrm)
            .where(ScriptOrm.project_id == project_id)
            .order_by(ScriptOrm.version.desc())
            .limit(1)
        )
        row = await self._session.scalar(stmt)
        return _to_domain(row) if row is not None else None

    async def list_for_project(self, project_id: uuid.UUID, params: PageParams) -> Page[Script]:
        stmt = (
            select(ScriptOrm)
            .where(ScriptOrm.project_id == project_id)
            .order_by(ScriptOrm.version.desc())
        )
        return await paginate(self._session, stmt, params, _to_domain)
