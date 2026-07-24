from __future__ import annotations

import uuid

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Trend


async def list_trends(uow: UnitOfWork, channel_id: uuid.UUID, params: PageParams) -> Page[Trend]:
    return await uow.trends.list_for_channel(channel_id, params)
