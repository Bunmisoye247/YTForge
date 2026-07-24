from __future__ import annotations

import uuid

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Scene, Storyboard


async def get_storyboard_for_project(uow: UnitOfWork, project_id: uuid.UUID) -> Storyboard:
    storyboard = await uow.storyboards.get_by_project(project_id)
    if storyboard is None:
        raise NotFoundError("Storyboard", project_id)
    return storyboard


async def list_scenes(uow: UnitOfWork, storyboard_id: uuid.UUID) -> list[Scene]:
    return await uow.scenes.list_for_storyboard(storyboard_id)
