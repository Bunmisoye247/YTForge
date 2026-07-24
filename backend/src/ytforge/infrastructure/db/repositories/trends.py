from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Trend
from ytforge.infrastructure.db.models import Trend as TrendOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: TrendOrm) -> Trend:
    return Trend(
        id=row.id,
        channel_id=row.channel_id,
        source=row.source,
        topic=row.topic,
        url=row.url,
        score=row.score,
        raw_payload=row.raw_payload,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyTrendRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, trend_id: uuid.UUID) -> Trend | None:
        row = await self._session.get(TrendOrm, trend_id)
        return _to_domain(row) if row is not None else None

    async def add(self, trend: Trend) -> None:
        row = TrendOrm(
            id=trend.id,
            channel_id=trend.channel_id,
            source=trend.source,
            topic=trend.topic,
            url=trend.url,
            score=trend.score,
            raw_payload=trend.raw_payload,
            created_at=trend.created_at,
            updated_at=trend.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def list_for_channel(self, channel_id: uuid.UUID, params: PageParams) -> Page[Trend]:
        stmt = (
            select(TrendOrm)
            .where(TrendOrm.channel_id == channel_id)
            .order_by(TrendOrm.score.desc())
        )
        return await paginate(self._session, stmt, params, _to_domain)
