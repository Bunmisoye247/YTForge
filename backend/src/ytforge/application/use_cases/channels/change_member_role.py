from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ChannelMember
from ytforge.domain.enums import ChannelRole


async def change_member_role(
    uow: UnitOfWork, channel_id: uuid.UUID, user_id: uuid.UUID, role: ChannelRole
) -> ChannelMember:
    member = await uow.channel_members.get(channel_id, user_id)
    if member is None:
        raise NotFoundError("ChannelMember", user_id)
    member.role = role
    member.updated_at = datetime.now(UTC)
    await uow.channel_members.update(member)
    await uow.commit()
    return member
