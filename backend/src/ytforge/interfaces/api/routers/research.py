from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.research import (
    AddResearchDocumentInput,
    add_research_document,
    list_research_documents,
)
from ytforge.domain.enums import ChannelRole
from ytforge.interfaces.api.deps.auth import require_project_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.schemas.pagination import PageResponse
from ytforge.interfaces.api.schemas.research import (
    ResearchDocumentCreateRequest,
    ResearchDocumentRead,
)

router = APIRouter(prefix="/projects/{project_id}/research", tags=["research"])


@router.post("", response_model=ResearchDocumentRead, status_code=status.HTTP_201_CREATED)
async def add(
    project_id: uuid.UUID,
    data: ResearchDocumentCreateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.EDITOR))],
) -> ResearchDocumentRead:
    try:
        document = await add_research_document(
            uow,
            AddResearchDocumentInput(
                project_id=project_id,
                source_url=data.source_url,
                title=data.title,
                content=data.content,
                citation=data.citation,
                published_at=data.published_at,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return ResearchDocumentRead.model_validate(document)


@router.get("", response_model=PageResponse[ResearchDocumentRead])
async def list_(
    project_id: uuid.UUID,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    _actor: Annotated[object, Depends(require_project_role(ChannelRole.VIEWER))],
) -> PageResponse[ResearchDocumentRead]:
    page = await list_research_documents(uow, project_id, params)
    return PageResponse.from_page(page, ResearchDocumentRead)
