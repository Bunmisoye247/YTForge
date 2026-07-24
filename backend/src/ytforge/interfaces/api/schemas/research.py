from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResearchDocumentCreateRequest(BaseModel):
    source_url: str = Field(min_length=1, max_length=2048)
    title: str = Field(min_length=1, max_length=500)
    content: str
    citation: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime | None = None


class ResearchDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    source_url: str
    title: str
    content: str
    citation: dict[str, Any]
    qdrant_point_id: str | None
    published_at: datetime | None
