from __future__ import annotations

import uuid

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Channel


async def list_channels_for_user(uow: UnitOfWork, user_id: uuid.UUID) -> list[Channel]:
    return await uow.channels.list_for_user(user_id)
