from __future__ import annotations

import uuid

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ResearchDocument


async def list_research_documents(
    uow: UnitOfWork, project_id: uuid.UUID, params: PageParams
) -> Page[ResearchDocument]:
    return await uow.research_documents.list_for_project(project_id, params)
