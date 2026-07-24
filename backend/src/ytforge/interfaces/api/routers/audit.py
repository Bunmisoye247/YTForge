from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.pagination import PageParams
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.audit import list_audit_logs
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.deps.pagination import page_params
from ytforge.interfaces.api.schemas.audit import AuditLogRead
from ytforge.interfaces.api.schemas.pagination import PageResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=PageResponse[AuditLogRead])
async def list_(
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    params: Annotated[PageParams, Depends(page_params)],
    entity_type: str,
    entity_id: uuid.UUID,
) -> PageResponse[AuditLogRead]:
    if not user.is_superuser:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "audit log access requires superuser")
    page = await list_audit_logs(uow, entity_type, entity_id, params)
    return PageResponse.from_page(page, AuditLogRead)
