from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Channel, ChannelMember
from ytforge.domain.enums import ChannelRole


@dataclass(frozen=True, slots=True)
class CreateChannelInput:
    name: str
    owner_user_id: uuid.UUID
    youtube_channel_id: str | None = None
    brand_kit: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)


async def create_channel(uow: UnitOfWork, data: CreateChannelInput) -> Channel:
    now = datetime.now(UTC)
    channel = Channel(
        id=uuid7(),
        name=data.name,
        youtube_channel_id=data.youtube_channel_id,
        brand_kit=data.brand_kit,
        defaults=data.defaults,
        created_at=now,
        updated_at=now,
    )
    await uow.channels.add(channel)
    await uow.channel_members.add(
        ChannelMember(
            id=uuid7(),
            channel_id=channel.id,
            user_id=data.owner_user_id,
            role=ChannelRole.OWNER,
            created_at=now,
            updated_at=now,
        )
    )
    await uow.commit()
    return channel
