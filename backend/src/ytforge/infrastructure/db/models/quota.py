from __future__ import annotations

import uuid
from datetime import date as date_

from sqlalchemy import Date, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ytforge.infrastructure.db.models.channels import Channel


class ApiQuotaLedger(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "api_quota_ledger"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    units_consumed: Mapped[int] = mapped_column(Integer, nullable=False)
    units_budget: Mapped[int] = mapped_column(Integer, nullable=False)

    channel: Mapped[Channel] = relationship()
