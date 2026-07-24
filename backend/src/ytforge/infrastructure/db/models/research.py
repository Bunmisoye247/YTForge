from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ytforge.infrastructure.db.models.projects import Project


class ResearchDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "research_documents"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(64))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship()
