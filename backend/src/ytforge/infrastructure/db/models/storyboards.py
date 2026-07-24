from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import StoryboardStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.projects import Project
from ytforge.infrastructure.db.models.scripts import Script


class Storyboard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "storyboards"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    script_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[StoryboardStatus] = mapped_column(
        pg_enum(StoryboardStatus, "storyboard_status"), nullable=False, default=StoryboardStatus.DRAFT
    )

    project: Mapped[Project] = relationship()
    script: Mapped[Script] = relationship()
    scenes: Mapped[list[Scene]] = relationship(
        back_populates="storyboard", cascade="all, delete-orphan", order_by="Scene.sequence_index"
    )


class Scene(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scenes"
    __table_args__ = (
        UniqueConstraint("storyboard_id", "sequence_index", name="uq_scenes_storyboard_sequence"),
    )

    storyboard_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("storyboards.id", ondelete="CASCADE"), nullable=False
    )
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    image_prompt: Mapped[str | None] = mapped_column(Text)
    video_prompt: Mapped[str | None] = mapped_column(Text)
    voice_line: Mapped[str | None] = mapped_column(Text)

    storyboard: Mapped[Storyboard] = relationship(back_populates="scenes")
