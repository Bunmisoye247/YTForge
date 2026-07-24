from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Project


class ProjectRepository(Protocol):
    async def get_by_id(self, project_id: uuid.UUID) -> Project | None: ...
    async def add(self, project: Project) -> None: ...
    async def update(self, project: Project) -> None: ...
    async def list_for_channel(
        self, channel_id: uuid.UUID, params: PageParams
    ) -> Page[Project]: ...
