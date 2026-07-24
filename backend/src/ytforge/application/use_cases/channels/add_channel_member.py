from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ChannelMember
from ytforge.domain.enums import ChannelRole


@dataclass(frozen=True, slots=True)
class AddChannelMemberInput:
    channel_id: uuid.UUID
    user_id: uuid.UUID
    role: ChannelRole


async def add_channel_member(uow: UnitOfWork, data: AddChannelMemberInput) -> ChannelMember:
    if await uow.channels.get_by_id(data.channel_id) is None:
        raise NotFoundError("Channel", data.channel_id)
    if await uow.channel_members.get(data.channel_id, data.user_id) is not None:
        raise ConflictError(f"user {data.user_id} is already a member of channel {data.channel_id}")

    now = datetime.now(UTC)
    member = ChannelMember(
        id=uuid7(),
        channel_id=data.channel_id,
        user_id=data.user_id,
        role=data.role,
        created_at=now,
        updated_at=now,
    )
    await uow.channel_members.add(member)
    await uow.commit()
    return member
