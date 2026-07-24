from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import VideoStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.assets import Asset
from ytforge.infrastructure.db.models.projects import Project


class Video(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "videos"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    render_asset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False
    )
    youtube_video_id: Mapped[str | None] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    synthetic_content_disclosure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[VideoStatus] = mapped_column(
        pg_enum(VideoStatus, "video_status"), nullable=False, default=VideoStatus.DRAFT
    )
    scheduled_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship()
    render_asset: Mapped[Asset] = relationship()
