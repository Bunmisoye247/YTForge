from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.fact_check import (
    RecordFactCheckInput,
    list_fact_checks_for_script,
    record_fact_check,
)
from ytforge.application.use_cases.scripts import (
    CreateScriptVersionInput,
    create_script_version,
    list_scripts,
    transition_script_status,
)
from ytforge.domain.enums import ChannelRole
from ytforge.interfaces.api.deps.auth import CurrentUser, require_project_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.schemas.pagination import PageResponse
from ytforge.interfaces.api.schemas.scripts import (
    FactCheckCreateRequest,
    FactCheckRead,
    ScriptCreateRequest,
    ScriptRead,
    ScriptStatusUpdateRequest,
)

router = APIRouter(tags=["scripts"])


@router.post(
    "/projects/{project_id}/scripts", response_model=ScriptRead, status_code=status.HTTP_201_CREATED
)
async def create(
    project_id: uuid.UUID,
    data: ScriptCreateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> ScriptRead:
    try:
        script = await create_script_version(
            uow,
            CreateScriptVersionInput(
                project_id=project_id,
                sections=data.sections,
                model_used=data.model_used,
                token_count=data.token_count,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return ScriptRead.model_validate(script)


@router.get("/projects/{project_id}/scripts", response_model=PageResponse[ScriptRead])
async def list_(
    project_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.VIEWER))],
) -> PageResponse[ScriptRead]:
    page = await list_scripts(uow, project_id, params)
    return PageResponse.from_page(page, ScriptRead)


@router.post("/scripts/{script_id}/status", response_model=ScriptRead)
async def update_status(
    script_id: uuid.UUID,
    data: ScriptStatusUpdateRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ScriptRead:
    try:
        script = await transition_script_status(uow, script_id, data.status)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return ScriptRead.model_validate(script)


@router.post(
    "/scripts/{script_id}/fact-checks",
    response_model=FactCheckRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_fact_check(
    script_id: uuid.UUID,
    data: FactCheckCreateRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> FactCheckRead:
    try:
        fact_check = await record_fact_check(
            uow,
            RecordFactCheckInput(
                script_id=script_id, verdict=data.verdict, flags=data.flags, model_used=data.model_used
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return FactCheckRead.model_validate(fact_check)


@router.get("/scripts/{script_id}/fact-checks", response_model=list[FactCheckRead])
async def list_fact_checks(
    script_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> list[FactCheckRead]:
    fact_checks = await list_fact_checks_for_script(uow, script_id)
    return [FactCheckRead.model_validate(fc) for fc in fact_checks]
