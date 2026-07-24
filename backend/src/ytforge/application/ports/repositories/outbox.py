from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.domain.entities import OutboxEvent


class OutboxRepository(Protocol):
    async def list_pending(self, limit: int = 100) -> list[OutboxEvent]: ...
    async def mark_published(self, event_id: uuid.UUID) -> None: ...
    async def mark_failed(self, event_id: uuid.UUID) -> None: ...
