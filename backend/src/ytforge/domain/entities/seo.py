from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, kw_only=True)
class SeoMetadata:
    id: uuid.UUID
    video_id: uuid.UUID
    title: str
    description: str
    created_at: datetime
    updated_at: datetime
    thumbnail_asset_id: uuid.UUID | None = None
    tags: list[Any] = field(default_factory=list)
    chapters: list[Any] = field(default_factory=list)
    keywords: list[Any] = field(default_factory=list)
