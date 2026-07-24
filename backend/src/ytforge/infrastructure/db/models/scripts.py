from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import ScriptStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.projects import Project


class Script(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scripts"
    __table_args__ = (UniqueConstraint("project_id", "version", name="uq_scripts_project_version"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ScriptStatus] = mapped_column(
        pg_enum(ScriptStatus, "script_status"), nullable=False, default=ScriptStatus.DRAFT
    )
    sections: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(128))
    token_count: Mapped[int | None] = mapped_column(Integer)

    project: Mapped[Project] = relationship()
