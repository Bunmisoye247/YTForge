from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    ip_address: str | None
