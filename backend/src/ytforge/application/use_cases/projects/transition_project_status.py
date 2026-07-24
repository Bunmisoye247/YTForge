from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Project
from ytforge.domain.enums import ProjectStatus
from ytforge.domain.errors import InvalidTransitionError


async def transition_project_status(
    uow: UnitOfWork, project_id: uuid.UUID, status: ProjectStatus
) -> Project:
    project = await uow.projects.get_by_id(project_id)
    if project is None:
        raise NotFoundError("Project", project_id)

    from_status = project.status
    try:
        project.transition_to(status)
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    project.updated_at = datetime.now(UTC)

    await uow.projects.update(project)
    await uow.add_event(
        aggregate_type="project",
        aggregate_id=project.id,
        event_type="ProjectStatusChanged",
        payload={"from_status": from_status.value, "to_status": status.value},
    )
    await uow.commit()
    return project
