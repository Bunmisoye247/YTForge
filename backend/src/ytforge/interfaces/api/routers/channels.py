from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.channels import (
    AddChannelMemberInput,
    CreateChannelInput,
    add_channel_member,
    change_member_role,
    create_channel,
    list_channels_for_user,
)
from ytforge.domain.enums import ChannelRole
from ytforge.interfaces.api.deps.auth import CurrentUser, require_channel_role
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.schemas.channels import (
    ChannelCreateRequest,
    ChannelMemberAddRequest,
    ChannelMemberRead,
    ChannelMemberRoleUpdateRequest,
    ChannelRead,
)

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post("", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def create(
    data: ChannelCreateRequest, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> ChannelRead:
    channel = await create_channel(
        uow,
        CreateChannelInput(
            name=data.name,
            owner_user_id=user.id,
            youtube_channel_id=data.youtube_channel_id,
            brand_kit=data.brand_kit,
            defaults=data.defaults,
        ),
    )
    return ChannelRead.model_validate(channel)


@router.get("", response_model=list[ChannelRead])
async def list_mine(
    user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> list[ChannelRead]:
    channels = await list_channels_for_user(uow, user.id)
    return [ChannelRead.model_validate(channel) for channel in channels]


@router.post(
    "/{channel_id}/members",
    response_model=ChannelMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    channel_id: uuid.UUID,
    data: ChannelMemberAddRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.ADMIN))],
) -> ChannelMemberRead:
    try:
        member = await add_channel_member(
            uow, AddChannelMemberInput(channel_id=channel_id, user_id=data.user_id, role=data.role)
        )
    except (NotFoundError, ConflictError) as exc:
        code = status.HTTP_404_NOT_FOUND if isinstance(exc, NotFoundError) else status.HTTP_409_CONFLICT
        raise HTTPException(code, str(exc)) from exc
    return ChannelMemberRead.model_validate(member)


@router.patch("/{channel_id}/members/{user_id}", response_model=ChannelMemberRead)
async def update_member_role(
    channel_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ChannelMemberRoleUpdateRequest,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    _actor: Annotated[object, Depends(require_channel_role(ChannelRole.ADMIN))],
) -> ChannelMemberRead:
    member = await change_member_role(uow, channel_id, user_id, data.role)
    return ChannelMemberRead.model_validate(member)
