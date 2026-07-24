from __future__ import annotations

import uuid

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Script


async def list_scripts(uow: UnitOfWork, project_id: uuid.UUID, params: PageParams) -> Page[Script]:
    return await uow.scripts.list_for_project(project_id, params)
