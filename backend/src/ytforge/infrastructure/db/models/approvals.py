from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import ApprovalKind, ApprovalStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.users import User


class Approval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "approvals"

    kind: Mapped[ApprovalKind] = mapped_column(pg_enum(ApprovalKind, "approval_kind"), nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(
        pg_enum(ApprovalStatus, "approval_status"), nullable=False, default=ApprovalStatus.PENDING
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    workflow_id: Mapped[str | None] = mapped_column(String(255))
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)

    requested_by: Mapped[User | None] = relationship(foreign_keys=[requested_by_user_id])
    decided_by: Mapped[User | None] = relationship(foreign_keys=[decided_by_user_id])
