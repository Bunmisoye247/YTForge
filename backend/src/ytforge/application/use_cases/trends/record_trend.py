from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Trend
from ytforge.domain.enums import TrendSource


@dataclass(frozen=True, slots=True)
class RecordTrendInput:
    source: TrendSource
    topic: str
    channel_id: uuid.UUID | None = None
    url: str | None = None
    score: float = 0.0
    raw_payload: dict[str, Any] = field(default_factory=dict)


async def record_trend(uow: UnitOfWork, data: RecordTrendInput) -> Trend:
    now = datetime.now(UTC)
    trend = Trend(
        id=uuid7(),
        channel_id=data.channel_id,
        source=data.source,
        topic=data.topic,
        url=data.url,
        score=data.score,
        raw_payload=data.raw_payload,
        created_at=now,
        updated_at=now,
    )
    await uow.trends.add(trend)
    await uow.commit()
    return trend
