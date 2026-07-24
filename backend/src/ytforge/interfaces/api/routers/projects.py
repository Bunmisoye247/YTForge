from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.projects import (
    CreateProjectInput,
    UpdateProjectInput,
    create_project,
    list_projects,
    transition_project_status,
    update_project,
)
from ytforge.domain.enums import ChannelRole
from ytforge.interfaces.api.deps.auth import CurrentUser, require_channel_role, require_project_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.schemas.pagination import PageResponse
from ytforge.interfaces.api.schemas.projects import (
    ProjectCreateRequest,
    ProjectRead,
    ProjectStatusUpdateRequest,
    ProjectUpdateRequest,
)

router = APIRouter(tags=["projects"])


@router.post(
    "/channels/{channel_id}/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED
)
async def create(
    channel_id: uuid.UUID,
    data: ProjectCreateRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.EDITOR))],
) -> ProjectRead:
    project = await create_project(
        uow,
        CreateProjectInput(
            channel_id=channel_id,
            title=data.title,
            created_by_user_id=user.id,
            trend_id=data.trend_id,
            budget_usd=data.budget_usd,
        ),
    )
    return ProjectRead.model_validate(project)


@router.get("/channels/{channel_id}/projects", response_model=PageResponse[ProjectRead])
async def list_for_channel(
    channel_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.VIEWER))],
) -> PageResponse[ProjectRead]:
    page = await list_projects(uow, channel_id, params)
    return PageResponse.from_page(page, ProjectRead)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
async def update(
    project_id: uuid.UUID,
    data: ProjectUpdateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> ProjectRead:
    try:
        project = await update_project(
            uow, project_id, UpdateProjectInput(title=data.title, budget_usd=data.budget_usd)
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return ProjectRead.model_validate(project)


@router.post("/projects/{project_id}/status", response_model=ProjectRead)
async def update_status(
    project_id: uuid.UUID,
    data: ProjectStatusUpdateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> ProjectRead:
    try:
        project = await transition_project_status(uow, project_id, data.status)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return ProjectRead.model_validate(project)
