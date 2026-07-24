from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Job


class JobRepository(Protocol):
    async def get_by_id(self, job_id: uuid.UUID) -> Job | None: ...
    async def list_for_project(
        self, project_id: uuid.UUID | None, params: PageParams
    ) -> Page[Job]: ...
    async def add(self, job: Job) -> None: ...
    async def update(self, job: Job) -> None: ...
