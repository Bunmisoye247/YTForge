from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import ModelAvailability, ModelCapability


@dataclass(slots=True, kw_only=True)
class ModelRegistryEntry:
    id: uuid.UUID
    provider: str
    model_name: str
    capability: ModelCapability
    status: ModelAvailability
    discovered_at: datetime
    created_at: datetime
    updated_at: datetime
    base_url: str | None = None
    last_checked_at: datetime | None = None
    entry_metadata: dict[str, Any] = field(default_factory=dict)
