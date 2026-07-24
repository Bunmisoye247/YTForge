from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import TrendSource


@dataclass(slots=True, kw_only=True)
class Trend:
    id: uuid.UUID
    channel_id: uuid.UUID | None
    source: TrendSource
    topic: str
    url: str | None
    score: float
    created_at: datetime
    updated_at: datetime
    raw_payload: dict[str, Any] = field(default_factory=dict)
