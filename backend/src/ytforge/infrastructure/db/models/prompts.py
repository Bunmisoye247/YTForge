from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import PromptRunStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.projects import Project


class PromptTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (UniqueConstraint("agent", "name", name="uq_prompt_templates_agent_name"),)

    agent: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    versions: Mapped[list[PromptVersion]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="PromptVersion.version"
    )


class PromptVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_prompt_versions_template_version"),
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("prompt_templates.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    front_matter: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    model_hints: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    variables: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    template: Mapped[PromptTemplate] = relationship(back_populates="versions")


class PromptRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prompt_runs"

    prompt_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("prompt_versions.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL")
    )
    input_variables: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    rendered_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text)
    model_used: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[PromptRunStatus] = mapped_column(
        pg_enum(PromptRunStatus, "prompt_run_status"), nullable=False
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))

    prompt_version: Mapped[PromptVersion] = relationship()
    project: Mapped[Project | None] = relationship()
