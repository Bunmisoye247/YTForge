from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, kw_only=True)
class ResearchDocument:
    id: uuid.UUID
    project_id: uuid.UUID
    source_url: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    citation: dict[str, Any] = field(default_factory=dict)
    qdrant_point_id: str | None = None
    published_at: datetime | None = None
