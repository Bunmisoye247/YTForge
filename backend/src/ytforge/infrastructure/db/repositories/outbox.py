from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import OutboxEvent
from ytforge.domain.enums import OutboxStatus
from ytforge.infrastructure.db.models import OutboxEvent as OutboxEventOrm


def _to_domain(row: OutboxEventOrm) -> OutboxEvent:
    return OutboxEvent(
        id=row.id,
        aggregate_type=row.aggregate_type,
        aggregate_id=row.aggregate_id,
        event_type=row.event_type,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        payload=row.payload,
        published_at=row.published_at,
    )


class SqlAlchemyOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_pending(self, limit: int = 100) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEventOrm)
            .where(OutboxEventOrm.status == OutboxStatus.PENDING)
            .order_by(OutboxEventOrm.created_at)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(row) for row in rows]

    async def mark_published(self, event_id: uuid.UUID) -> None:
        row = await self._session.get(OutboxEventOrm, event_id)
        assert row is not None
        row.status = OutboxStatus.PUBLISHED
        row.published_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_failed(self, event_id: uuid.UUID) -> None:
        row = await self._session.get(OutboxEventOrm, event_id)
        assert row is not None
        row.status = OutboxStatus.FAILED
        await self._session.flush()
