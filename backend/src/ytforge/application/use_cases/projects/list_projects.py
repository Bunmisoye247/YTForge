from __future__ import annotations

import uuid

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Project


async def list_projects(uow: UnitOfWork, channel_id: uuid.UUID, params: PageParams) -> Page[Project]:
    return await uow.projects.list_for_channel(channel_id, params)
