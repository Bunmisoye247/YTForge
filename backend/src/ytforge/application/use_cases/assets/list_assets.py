from __future__ import annotations

import uuid

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Asset


async def list_assets(uow: UnitOfWork, project_id: uuid.UUID, params: PageParams) -> Page[Asset]:
    return await uow.assets.list_for_project(project_id, params)
