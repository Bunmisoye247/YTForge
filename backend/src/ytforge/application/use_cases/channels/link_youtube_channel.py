from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Channel


@dataclass(frozen=True, slots=True)
class LinkYouTubeChannelInput:
    youtube_channel_id: str
    refresh_token: str


async def link_youtube_channel(uow: UnitOfWork, channel_id: uuid.UUID, data: LinkYouTubeChannelInput) -> Channel:
    """Called after the Google OAuth callback exchanges an authorization
    code for a refresh token (ARCHITECTURE.md §7.1's "Google OAuth for
    YouTube channel linking"). The repository envelope-encrypts
    `refresh_token` before it ever reaches the database."""
    channel = await uow.channels.get_by_id(channel_id)
    if channel is None:
        raise NotFoundError("Channel", channel_id)

    channel.youtube_channel_id = data.youtube_channel_id
    channel.oauth_refresh_token = data.refresh_token
    channel.updated_at = datetime.now(UTC)

    await uow.channels.update(channel)
    await uow.add_event(
        aggregate_type="channel",
        aggregate_id=channel.id,
        event_type="YouTubeChannelLinked",
        payload={"youtube_channel_id": data.youtube_channel_id},
    )
    await uow.commit()
    return channel
