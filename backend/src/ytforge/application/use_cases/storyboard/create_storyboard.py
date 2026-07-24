from __future__ import annotations

import uuid
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Storyboard
from ytforge.domain.enums import StoryboardStatus


async def create_storyboard(uow: UnitOfWork, project_id: uuid.UUID, script_id: uuid.UUID) -> Storyboard:
    if await uow.projects.get_by_id(project_id) is None:
        raise NotFoundError("Project", project_id)
    if await uow.scripts.get_by_id(script_id) is None:
        raise NotFoundError("Script", script_id)
    if await uow.storyboards.get_by_project(project_id) is not None:
        raise ConflictError(f"project {project_id} already has a storyboard")

    now = datetime.now(UTC)
    storyboard = Storyboard(
        id=uuid7(),
        project_id=project_id,
        script_id=script_id,
        status=StoryboardStatus.DRAFT,
        created_at=now,
        updated_at=now,
    )
    await uow.storyboards.add(storyboard)
    await uow.commit()
    return storyboard
