from __future__ import annotations

import uuid
from datetime import date as date_

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import ApiQuotaLedger
from ytforge.infrastructure.db.models import ApiQuotaLedger as ApiQuotaLedgerOrm


def _to_domain(row: ApiQuotaLedgerOrm) -> ApiQuotaLedger:
    return ApiQuotaLedger(
        id=row.id,
        channel_id=row.channel_id,
        date=row.date,
        operation=row.operation,
        units_consumed=row.units_consumed,
        units_budget=row.units_budget,
    )


class SqlAlchemyApiQuotaLedgerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_channel(
        self, channel_id: uuid.UUID, start: date_, end: date_
    ) -> list[ApiQuotaLedger]:
        stmt = (
            select(ApiQuotaLedgerOrm)
            .where(
                ApiQuotaLedgerOrm.channel_id == channel_id,
                ApiQuotaLedgerOrm.date >= start,
                ApiQuotaLedgerOrm.date <= end,
            )
            .order_by(ApiQuotaLedgerOrm.date)
        )
        rows = await self._session.scalars(stmt)
        return [_to_domain(row) for row in rows]

    async def add(self, entry: ApiQuotaLedger) -> None:
        self._session.add(
            ApiQuotaLedgerOrm(
                id=entry.id,
                channel_id=entry.channel_id,
                date=entry.date,
                operation=entry.operation,
                units_consumed=entry.units_consumed,
                units_budget=entry.units_budget,
            )
        )
        await self._session.flush()
