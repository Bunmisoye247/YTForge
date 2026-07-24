from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import ProjectStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.channels import Channel
from ytforge.infrastructure.db.models.trends import Trend
from ytforge.infrastructure.db.models.users import User


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    trend_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("trends.id", ondelete="SET NULL")
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        pg_enum(ProjectStatus, "project_status"), nullable=False, default=ProjectStatus.IDEA
    )
    budget_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    channel: Mapped[Channel] = relationship()
    trend: Mapped[Trend | None] = relationship()
    created_by: Mapped[User | None] = relationship()
