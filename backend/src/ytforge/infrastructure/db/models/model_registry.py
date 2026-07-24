from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ytforge.domain.enums import ModelAvailability, ModelCapability
from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class ModelRegistryEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "model_registry"
    __table_args__ = (
        UniqueConstraint("provider", "model_name", "capability", name="uq_model_registry_provider_model_cap"),
    )

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    capability: Mapped[ModelCapability] = mapped_column(
        pg_enum(ModelCapability, "model_capability"), nullable=False
    )
    base_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[ModelAvailability] = mapped_column(
        pg_enum(ModelAvailability, "model_availability"),
        nullable=False,
        default=ModelAvailability.UNAVAILABLE,
    )
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
