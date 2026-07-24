from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ytforge.domain.enums import ModelAvailability, ModelCapability


class ModelRegisterRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    model_name: str = Field(min_length=1, max_length=255)
    capability: ModelCapability
    base_url: str | None = None
    status: ModelAvailability = ModelAvailability.AVAILABLE
    entry_metadata: dict[str, Any] = Field(default_factory=dict)


class ModelStatusUpdateRequest(BaseModel):
    status: ModelAvailability


class ModelRegistryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    model_name: str
    capability: ModelCapability
    status: ModelAvailability
    discovered_at: datetime
    base_url: str | None
    last_checked_at: datetime | None
    entry_metadata: dict[str, Any]
