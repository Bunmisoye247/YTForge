from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import ResearchDocument


class ResearchDocumentRepository(Protocol):
    async def get_by_id(self, document_id: uuid.UUID) -> ResearchDocument | None: ...
    async def add(self, document: ResearchDocument) -> None: ...
    async def list_for_project(
        self, project_id: uuid.UUID, params: PageParams
    ) -> Page[ResearchDocument]: ...
