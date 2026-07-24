from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, LargeBinary, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import ChannelRole
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.users import User


class Channel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "channels"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    youtube_channel_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    brand_kit: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    defaults: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Envelope encryption: each record's OAuth refresh token is encrypted with a
    # per-record data key (DEK), which is itself encrypted by an external master
    # key (KEK). Only the two ciphertexts + key version are ever persisted.
    oauth_refresh_token_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    oauth_refresh_token_nonce: Mapped[bytes | None] = mapped_column(LargeBinary)
    data_key_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)
    encryption_key_version: Mapped[int | None] = mapped_column(Integer)

    members: Mapped[list[ChannelMember]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )


class ChannelMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "channel_members"
    __table_args__ = (UniqueConstraint("channel_id", "user_id", name="uq_channel_members_channel_user"),)

    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[ChannelRole] = mapped_column(
        pg_enum(ChannelRole, "channel_role"), nullable=False
    )

    channel: Mapped[Channel] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="channel_memberships")
