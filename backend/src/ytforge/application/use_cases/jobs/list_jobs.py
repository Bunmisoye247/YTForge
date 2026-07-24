from __future__ import annotations

import uuid

from ytforge.application.common.pagination import Page, PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Job


async def list_jobs(uow: UnitOfWork, project_id: uuid.UUID | None, params: PageParams) -> Page[Job]:
    """Read-only mirror of Temporal workflow runs. `start`/`cancel`/`signal`
    require a live Temporal client — added in Phase 7."""
    return await uow.jobs.list_for_project(project_id, params)
