from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.prompts import (
    CreatePromptVersionInput,
    RecordPromptRunInput,
    create_prompt_version,
    list_prompt_templates,
    list_prompt_versions,
    record_prompt_run,
)
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.schemas.prompts import (
    PromptRunCreateRequest,
    PromptRunRead,
    PromptTemplateRead,
    PromptVersionCreateRequest,
    PromptVersionRead,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/templates", response_model=list[PromptTemplateRead])
async def list_templates(
    user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> list[PromptTemplateRead]:
    templates = await list_prompt_templates(uow)
    return [PromptTemplateRead.model_validate(t) for t in templates]


@router.get("/templates/{template_id}/versions", response_model=list[PromptVersionRead])
async def list_versions(
    template_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> list[PromptVersionRead]:
    versions = await list_prompt_versions(uow, template_id)
    return [PromptVersionRead.model_validate(v) for v in versions]


@router.post("/versions", response_model=PromptVersionRead, status_code=status.HTTP_201_CREATED)
async def create_version(
    data: PromptVersionCreateRequest, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> PromptVersionRead:
    version = await create_prompt_version(
        uow,
        CreatePromptVersionInput(
            agent=data.agent,
            name=data.name,
            content=data.content,
            front_matter=data.front_matter,
            model_hints=data.model_hints,
            variables=data.variables,
        ),
    )
    return PromptVersionRead.model_validate(version)


@router.post("/runs", response_model=PromptRunRead, status_code=status.HTTP_201_CREATED)
async def record_run(
    data: PromptRunCreateRequest, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> PromptRunRead:
    run = await record_prompt_run(
        uow,
        RecordPromptRunInput(
            prompt_version_id=data.prompt_version_id,
            input_variables=data.input_variables,
            rendered_prompt=data.rendered_prompt,
            model_used=data.model_used,
            status=data.status,
            project_id=data.project_id,
            response=data.response,
            latency_ms=data.latency_ms,
            cost_usd=data.cost_usd,
        ),
    )
    return PromptRunRead.model_validate(run)
