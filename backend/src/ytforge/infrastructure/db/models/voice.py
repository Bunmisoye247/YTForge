from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import VoiceProfileStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.assets import Asset
from ytforge.infrastructure.db.models.channels import Channel
from ytforge.infrastructure.db.models.projects import Project
from ytforge.infrastructure.db.models.storyboards import Scene


class VoiceProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "voice_profiles"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_voice_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[VoiceProfileStatus] = mapped_column(
        pg_enum(VoiceProfileStatus, "voice_profile_status"),
        nullable=False,
        default=VoiceProfileStatus.PENDING_APPROVAL,
    )
    consent_artifact_object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    consent_recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    channel: Mapped[Channel] = relationship()


class Voiceover(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "voiceovers"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL")
    )
    voice_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("voice_profiles.id", ondelete="SET NULL")
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    word_timestamps: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    duration_seconds: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    project: Mapped[Project] = relationship()
    scene: Mapped[Scene | None] = relationship()
    voice_profile: Mapped[VoiceProfile | None] = relationship()
    asset: Mapped[Asset] = relationship()
