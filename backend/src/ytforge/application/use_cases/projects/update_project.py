from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Project


@dataclass(frozen=True, slots=True)
class UpdateProjectInput:
    title: str | None = None
    budget_usd: Decimal | None = None


async def update_project(uow: UnitOfWork, project_id: uuid.UUID, data: UpdateProjectInput) -> Project:
    project = await uow.projects.get_by_id(project_id)
    if project is None:
        raise NotFoundError("Project", project_id)

    if data.title is not None:
        project.title = data.title
    if data.budget_usd is not None:
        project.budget_usd = data.budget_usd
    project.updated_at = datetime.now(UTC)

    await uow.projects.update(project)
    await uow.commit()
    return project
