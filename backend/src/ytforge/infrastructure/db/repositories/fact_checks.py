from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import FactCheck
from ytforge.infrastructure.db.models import FactCheck as FactCheckOrm


def _to_domain(row: FactCheckOrm) -> FactCheck:
    return FactCheck(
        id=row.id,
        script_id=row.script_id,
        script_version=row.script_version,
        verdict=row.verdict,
        flags=row.flags,
        model_used=row.model_used,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyFactCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, fact_check: FactCheck) -> None:
        row = FactCheckOrm(
            id=fact_check.id,
            script_id=fact_check.script_id,
            script_version=fact_check.script_version,
            verdict=fact_check.verdict,
            flags=fact_check.flags,
            model_used=fact_check.model_used,
            created_at=fact_check.created_at,
            updated_at=fact_check.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def list_for_script(self, script_id: uuid.UUID) -> list[FactCheck]:
        stmt = (
            select(FactCheckOrm)
            .where(FactCheckOrm.script_id == script_id)
            .order_by(FactCheckOrm.created_at.desc())
        )
        rows = await self._session.scalars(stmt)
        return [_to_domain(row) for row in rows]
