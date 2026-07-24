from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.domain.enums import FactCheckVerdict
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum
from ytforge.infrastructure.db.models.scripts import Script


class FactCheck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fact_checks"

    script_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False
    )
    script_version: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[FactCheckVerdict] = mapped_column(
        pg_enum(FactCheckVerdict, "fact_check_verdict"), nullable=False
    )
    flags: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(128))

    script: Mapped[Script] = relationship()
