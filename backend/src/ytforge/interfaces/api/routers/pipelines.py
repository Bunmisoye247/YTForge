from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from temporalio.client import Client

from ytforge.application.common.errors import NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.jobs import get_job, list_jobs
from ytforge.infrastructure.config.settings import get_settings
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.deps.temporal import get_temporal_client
from ytforge.interfaces.api.schemas.pagination import PageResponse
from ytforge.interfaces.api.schemas.pipelines import (
    JobRead,
    StartPipelineRequest,
    StartPipelineResponse,
)
from ytforge.interfaces.workflows import VideoProductionWorkflow, VideoProductionWorkflowInput

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("", response_model=PageResponse[JobRead])
async def list_(
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    project_id: uuid.UUID | None = None,
) -> PageResponse[JobRead]:
    page = await list_jobs(uow, project_id, params)
    return PageResponse.from_page(page, JobRead)


@router.get("/{job_id}", response_model=JobRead)
async def get_(
    job_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> JobRead:
    try:
        job = await get_job(uow, job_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return JobRead.model_validate(job)


@router.post("", response_model=StartPipelineResponse, status_code=status.HTTP_201_CREATED)
async def start_(
    data: StartPipelineRequest,
    user: CurrentUser,
    client: Annotated[Client, Depends(get_temporal_client)],
) -> StartPipelineResponse:
    """Starts a `VideoProductionWorkflow` run. A `jobs` row is created by
    the workflow itself (its first activity) — not here — so `GET
    /pipelines` reflects reality even if this request's response never
    reaches the caller."""
    settings = get_settings()
    workflow_id = f"video-production-{data.project_id}-{uuid.uuid4().hex[:8]}"
    handle = await client.start_workflow(
        VideoProductionWorkflow.run,
        VideoProductionWorkflowInput(
            project_id=str(data.project_id), topic=data.topic, requested_by_user_id=str(user.id)
        ),
        id=workflow_id,
        task_queue=settings.temporal.task_queue,
    )
    return StartPipelineResponse(workflow_id=handle.id, run_id=handle.result_run_id)


@router.post("/{job_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_(
    job_id: uuid.UUID,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    client: Annotated[Client, Depends(get_temporal_client)],
) -> None:
    try:
        job = await get_job(uow, job_id)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    handle = client.get_workflow_handle(job.temporal_workflow_id, run_id=job.temporal_run_id)
    await handle.cancel()
