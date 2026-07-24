from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ModelRegistryEntry
from ytforge.domain.enums import ModelAvailability


async def update_model_status(
    uow: UnitOfWork, entry_id: uuid.UUID, status: ModelAvailability
) -> ModelRegistryEntry:
    entry = await uow.model_registry.get_by_id(entry_id)
    if entry is None:
        raise NotFoundError("ModelRegistryEntry", entry_id)

    now = datetime.now(UTC)
    entry.status = status
    entry.last_checked_at = now
    entry.updated_at = now
    await uow.model_registry.update(entry)
    await uow.commit()
    return entry
