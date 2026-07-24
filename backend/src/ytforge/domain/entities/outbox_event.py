from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import OutboxStatus


@dataclass(slots=True)
class OutboxEvent:
    id: uuid.UUID
    aggregate_type: str
    aggregate_id: uuid.UUID
    event_type: str
    status: OutboxStatus
    created_at: datetime
    updated_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None
