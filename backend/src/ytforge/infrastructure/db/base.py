from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid6 import uuid7


class Base(DeclarativeBase):
    pass


def pg_enum[E: enum.Enum](enum_cls: type[E], name: str) -> SqlEnum:
    """A Postgres ENUM type that persists member .value rather than .name."""
    return SqlEnum(enum_cls, name=name, values_callable=lambda cls: [e.value for e in cls])


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid7
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
