from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import AuditLog


class AuditLogRepository(Protocol):
    async def add(self, entry: AuditLog) -> None: ...
    async def list_for_entity(
        self, entity_type: str, entity_id: uuid.UUID, params: PageParams
    ) -> Page[AuditLog]: ...
