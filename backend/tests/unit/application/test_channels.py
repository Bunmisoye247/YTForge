from __future__ import annotations

import pytest
from uuid6 import uuid7

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.errors import ConflictError, NotFoundError
from ytforge.application.use_cases.channels import (
    AddChannelMemberInput,
    CreateChannelInput,
    LinkYouTubeChannelInput,
    add_channel_member,
    change_member_role,
    create_channel,
    link_youtube_channel,
    list_channels_for_user,
)
from ytforge.domain.enums import ChannelRole


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def test_create_channel_adds_owner_membership(uow: FakeUnitOfWork) -> None:
    owner_id = uuid7()
    channel = await create_channel(uow, CreateChannelInput(name="My Channel", owner_user_id=owner_id))

    channels = await list_channels_for_user(uow, owner_id)
    assert channels == [channel]

    member = await uow.channel_members.get(channel.id, owner_id)
    assert member is not None
    assert member.role == ChannelRole.OWNER


async def test_add_channel_member_requires_existing_channel(uow: FakeUnitOfWork) -> None:
    with pytest.raises(NotFoundError):
        await add_channel_member(
            uow, AddChannelMemberInput(channel_id=uuid7(), user_id=uuid7(), role=ChannelRole.EDITOR)
        )


async def test_add_channel_member_rejects_duplicate(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="My Channel", owner_user_id=uuid7()))
    user_id = uuid7()
    await add_channel_member(
        uow, AddChannelMemberInput(channel_id=channel.id, user_id=user_id, role=ChannelRole.EDITOR)
    )
    with pytest.raises(ConflictError):
        await add_channel_member(
            uow, AddChannelMemberInput(channel_id=channel.id, user_id=user_id, role=ChannelRole.VIEWER)
        )


async def test_change_member_role(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="My Channel", owner_user_id=uuid7()))
    user_id = uuid7()
    await add_channel_member(
        uow, AddChannelMemberInput(channel_id=channel.id, user_id=user_id, role=ChannelRole.VIEWER)
    )
    updated = await change_member_role(uow, channel.id, user_id, ChannelRole.EDITOR)
    assert updated.role == ChannelRole.EDITOR


async def test_link_youtube_channel_sets_id_and_token(uow: FakeUnitOfWork) -> None:
    channel = await create_channel(uow, CreateChannelInput(name="My Channel", owner_user_id=uuid7()))

    updated = await link_youtube_channel(
        uow, channel.id, LinkYouTubeChannelInput(youtube_channel_id="UC-abc123", refresh_token="refresh-token-1")
    )

    assert updated.youtube_channel_id == "UC-abc123"
    assert updated.oauth_refresh_token == "refresh-token-1"
    assert any(e["event_type"] == "YouTubeChannelLinked" for e in uow.events)


async def test_link_youtube_channel_requires_existing_channel(uow: FakeUnitOfWork) -> None:
    with pytest.raises(NotFoundError):
        await link_youtube_channel(
            uow, uuid7(), LinkYouTubeChannelInput(youtube_channel_id="UC-abc123", refresh_token="refresh-token-1")
        )
