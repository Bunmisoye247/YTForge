from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ytforge.infrastructure.db.models.users import User


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)

    actor: Mapped[User | None] = relationship()
