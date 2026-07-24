from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from temporalio.client import Client

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.approvals import (
    DecideApprovalInput,
    RequestApprovalInput,
    decide_approval,
    list_approvals,
    request_approval,
)
from ytforge.domain.enums import ApprovalStatus
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.deps.temporal import get_optional_temporal_client
from ytforge.interfaces.api.schemas.approvals import (
    ApprovalDecisionRequest,
    ApprovalRead,
    ApprovalRequestRequest,
)
from ytforge.interfaces.api.schemas.pagination import PageResponse
from ytforge.interfaces.workflows import VideoProductionWorkflow

logger = logging.getLogger("ytforge.approvals")

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.post("", response_model=ApprovalRead, status_code=status.HTTP_201_CREATED)
async def request_(
    data: ApprovalRequestRequest, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ApprovalRead:
    approval = await request_approval(
        uow,
        RequestApprovalInput(
            kind=data.kind, requested_by_user_id=user.id, payload=data.payload, workflow_id=data.workflow_id
        ),
    )
    return ApprovalRead.model_validate(approval)


@router.get("", response_model=PageResponse[ApprovalRead])
async def list_(
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: ApprovalStatus | None = None,
) -> PageResponse[ApprovalRead]:
    page = await list_approvals(uow, status_filter, params)
    return PageResponse.from_page(page, ApprovalRead)


@router.post("/{approval_id}/decision", response_model=ApprovalRead)
async def decide(
    approval_id: uuid.UUID,
    data: ApprovalDecisionRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    temporal_client: Annotated[Client | None, Depends(get_optional_temporal_client)],
) -> ApprovalRead:
    try:
        approval = await decide_approval(
            uow,
            approval_id,
            DecideApprovalInput(status=data.status, decided_by_user_id=user.id, note=data.note),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    if approval.workflow_id and temporal_client is not None:
        try:
            handle = temporal_client.get_workflow_handle(approval.workflow_id)
            await handle.signal(
                VideoProductionWorkflow.approval_decided, args=[str(approval.id), data.status.value]
            )
        except Exception:
            # The DB decision already committed — a workflow that can't be
            # signaled (already completed, Temporal hiccup) shouldn't turn
            # a successful decision into a 500; it's logged for an operator
            # to notice and, if needed, replay.
            logger.exception("failed to signal workflow %s for approval %s", approval.workflow_id, approval.id)

    return ApprovalRead.model_validate(approval)
