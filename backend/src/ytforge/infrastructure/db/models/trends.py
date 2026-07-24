from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import TrendSource
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.channels import Channel


class Trend(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trends"

    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("channels.id", ondelete="SET NULL")
    )
    source: Mapped[TrendSource] = mapped_column(pg_enum(TrendSource, "trend_source"), nullable=False)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    channel: Mapped[Channel | None] = relationship()
