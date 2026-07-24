from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import TrendSource


class TrendCreateRequest(BaseModel):
    source: TrendSource
    topic: str = Field(min_length=1, max_length=500)
    url: str | None = None
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class TrendRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_id: uuid.UUID | None
    source: TrendSource
    topic: str
    url: str | None
    score: float
    raw_payload: dict[str, Any]
