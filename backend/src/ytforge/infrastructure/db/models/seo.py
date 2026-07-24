from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ytforge.infrastructure.db.models.assets import Asset
from ytforge.infrastructure.db.models.videos import Video


class SeoMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "seo_metadata"

    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    thumbnail_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    tags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    chapters: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    keywords: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    video: Mapped[Video] = relationship()
    thumbnail_asset: Mapped[Asset | None] = relationship()
