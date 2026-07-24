from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ytforge.domain.enums import OutboxStatus
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class OutboxEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "outbox"

    aggregate_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        pg_enum(OutboxStatus, "outbox_status"), nullable=False, default=OutboxStatus.PENDING
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
