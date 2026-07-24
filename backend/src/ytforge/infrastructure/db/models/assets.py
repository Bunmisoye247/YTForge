from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import AssetStatus, AssetType
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.projects import Project
from ytforge.infrastructure.db.models.storyboards import Scene


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assets"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL")
    )
    asset_type: Mapped[AssetType] = mapped_column(pg_enum(AssetType, "asset_type"), nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        pg_enum(AssetStatus, "asset_status"), nullable=False, default=AssetStatus.PENDING
    )
    bucket: Mapped[str] = mapped_column(String(63), nullable=False)
    object_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    project: Mapped[Project] = relationship()
    scene: Mapped[Scene | None] = relationship()
