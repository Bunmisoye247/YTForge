from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import Channel, ChannelMember
from ytforge.infrastructure.db.models import Channel as ChannelOrm
from ytforge.infrastructure.db.models import ChannelMember as ChannelMemberOrm
from ytforge.infrastructure.security.encryption import EncryptedSecret, get_envelope_encryptor


def _channel_to_domain(row: ChannelOrm) -> Channel:
    refresh_token: str | None = None
    if row.oauth_refresh_token_ciphertext is not None:
        assert row.oauth_refresh_token_nonce is not None
        assert row.data_key_ciphertext is not None
        assert row.encryption_key_version is not None
        refresh_token = get_envelope_encryptor().decrypt(
            EncryptedSecret(
                ciphertext=row.oauth_refresh_token_ciphertext,
                nonce=row.oauth_refresh_token_nonce,
                data_key_ciphertext=row.data_key_ciphertext,
                key_version=row.encryption_key_version,
            )
        )
    return Channel(
        id=row.id,
        name=row.name,
        youtube_channel_id=row.youtube_channel_id,
        brand_kit=row.brand_kit,
        defaults=row.defaults,
        created_at=row.created_at,
        updated_at=row.updated_at,
        oauth_refresh_token=refresh_token,
    )


def _apply_refresh_token(row: ChannelOrm, channel: Channel) -> None:
    if channel.oauth_refresh_token is None:
        row.oauth_refresh_token_ciphertext = None
        row.oauth_refresh_token_nonce = None
        row.data_key_ciphertext = None
        row.encryption_key_version = None
        return
    secret = get_envelope_encryptor().encrypt(channel.oauth_refresh_token)
    row.oauth_refresh_token_ciphertext = secret.ciphertext
    row.oauth_refresh_token_nonce = secret.nonce
    row.data_key_ciphertext = secret.data_key_ciphertext
    row.encryption_key_version = secret.key_version


def _member_to_domain(row: ChannelMemberOrm) -> ChannelMember:
    return ChannelMember(
        id=row.id,
        channel_id=row.channel_id,
        user_id=row.user_id,
        role=row.role,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, channel_id: uuid.UUID) -> Channel | None:
        row = await self._session.get(ChannelOrm, channel_id)
        return _channel_to_domain(row) if row is not None else None

    async def add(self, channel: Channel) -> None:
        row = ChannelOrm(
            id=channel.id,
            name=channel.name,
            youtube_channel_id=channel.youtube_channel_id,
            brand_kit=channel.brand_kit,
            defaults=channel.defaults,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )
        _apply_refresh_token(row, channel)
        self._session.add(row)
        await self._session.flush()

    async def update(self, channel: Channel) -> None:
        row = await self._session.get(ChannelOrm, channel.id)
        assert row is not None
        row.name = channel.name
        row.youtube_channel_id = channel.youtube_channel_id
        row.brand_kit = channel.brand_kit
        row.defaults = channel.defaults
        row.updated_at = channel.updated_at
        _apply_refresh_token(row, channel)
        await self._session.flush()

    async def list_for_user(self, user_id: uuid.UUID) -> list[Channel]:
        stmt = (
            select(ChannelOrm)
            .join(ChannelMemberOrm, ChannelMemberOrm.channel_id == ChannelOrm.id)
            .where(ChannelMemberOrm.user_id == user_id)
            .order_by(ChannelOrm.created_at.desc())
        )
        rows = await self._session.scalars(stmt)
        return [_channel_to_domain(row) for row in rows]


class SqlAlchemyChannelMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, channel_id: uuid.UUID, user_id: uuid.UUID) -> ChannelMember | None:
        stmt = select(ChannelMemberOrm).where(
            ChannelMemberOrm.channel_id == channel_id, ChannelMemberOrm.user_id == user_id
        )
        row = await self._session.scalar(stmt)
        return _member_to_domain(row) if row is not None else None

    async def add(self, member: ChannelMember) -> None:
        row = ChannelMemberOrm(
            id=member.id,
            channel_id=member.channel_id,
            user_id=member.user_id,
            role=member.role,
            created_at=member.created_at,
            updated_at=member.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, member: ChannelMember) -> None:
        row = await self._session.get(ChannelMemberOrm, member.id)
        assert row is not None
        row.role = member.role
        row.updated_at = member.updated_at
        await self._session.flush()

    async def list_for_channel(self, channel_id: uuid.UUID) -> list[ChannelMember]:
        stmt = select(ChannelMemberOrm).where(ChannelMemberOrm.channel_id == channel_id)
        rows = await self._session.scalars(stmt)
        return [_member_to_domain(row) for row in rows]
