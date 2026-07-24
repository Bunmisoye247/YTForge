from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import JobStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.projects import Project


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"

    temporal_workflow_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    temporal_run_id: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL")
    )
    status: Mapped[JobStatus] = mapped_column(
        pg_enum(JobStatus, "job_status"), nullable=False, default=JobStatus.RUNNING
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)

    project: Mapped[Project | None] = relationship()
