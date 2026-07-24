from __future__ import annotations

import uuid

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.enums import ChannelRole

_ROLE_RANK: dict[ChannelRole, int] = {
    ChannelRole.VIEWER: 0,
    ChannelRole.EDITOR: 1,
    ChannelRole.ADMIN: 2,
    ChannelRole.OWNER: 3,
}


async def resolve_channel_role(
    uow: UnitOfWork, user_id: uuid.UUID, channel_id: uuid.UUID
) -> ChannelRole | None:
    member = await uow.channel_members.get(channel_id, user_id)
    return member.role if member is not None else None


def role_satisfies(actual: ChannelRole, minimum: ChannelRole) -> bool:
    """owner > admin > editor > viewer — `actual` must be at least as senior
    as `minimum`."""
    return _ROLE_RANK[actual] >= _ROLE_RANK[minimum]
