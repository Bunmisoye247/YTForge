from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import AuditLog
from ytforge.infrastructure.db.models import AuditLog as AuditLogOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: AuditLogOrm) -> AuditLog:
    return AuditLog(
        id=row.id,
        actor_user_id=row.actor_user_id,
        action=row.action,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        before=row.before,
        after=row.after,
        ip_address=row.ip_address,
    )


class SqlAlchemyAuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: AuditLog) -> None:
        row = AuditLogOrm(
            id=entry.id,
            actor_user_id=entry.actor_user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            before=entry.before,
            after=entry.after,
            ip_address=entry.ip_address,
        )
        self._session.add(row)
        await self._session.flush()

    async def list_for_entity(
        self, entity_type: str, entity_id: uuid.UUID, params: PageParams
    ) -> Page[AuditLog]:
        stmt = (
            select(AuditLogOrm)
            .where(AuditLogOrm.entity_type == entity_type, AuditLogOrm.entity_id == entity_id)
            .order_by(AuditLogOrm.created_at.desc())
        )
        return await paginate(self._session, stmt, params, _to_domain)
