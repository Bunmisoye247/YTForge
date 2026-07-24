from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.model_registry import (
    RegisterModelInput,
    list_models,
    register_model,
    update_model_status,
)
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.schemas.models import (
    ModelRegisterRequest,
    ModelRegistryEntryRead,
    ModelStatusUpdateRequest,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.post("", response_model=ModelRegistryEntryRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: ModelRegisterRequest, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ModelRegistryEntryRead:
    """Manual registration. Auto-detection (ModelRouter discovery scan)
    lands in Phase 6."""
    entry = await register_model(
        uow,
        RegisterModelInput(
            provider=data.provider,
            model_name=data.model_name,
            capability=data.capability,
            base_url=data.base_url,
            status=data.status,
            entry_metadata=data.entry_metadata,
        ),
    )
    return ModelRegistryEntryRead.model_validate(entry)


@router.get("", response_model=list[ModelRegistryEntryRead])
async def list_(
    user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> list[ModelRegistryEntryRead]:
    entries = await list_models(uow)
    return [ModelRegistryEntryRead.model_validate(entry) for entry in entries]


@router.patch("/{entry_id}/status", response_model=ModelRegistryEntryRead)
async def update_status(
    entry_id: uuid.UUID,
    data: ModelStatusUpdateRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ModelRegistryEntryRead:
    try:
        entry = await update_model_status(uow, entry_id, data.status)
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return ModelRegistryEntryRead.model_validate(entry)
