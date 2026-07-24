from __future__ import annotations

import uuid

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import AuditLog


async def list_audit_logs(
    uow: UnitOfWork, entity_type: str, entity_id: uuid.UUID, params: PageParams
) -> Page[AuditLog]:
    return await uow.audit_logs.list_for_entity(entity_type, entity_id, params)
