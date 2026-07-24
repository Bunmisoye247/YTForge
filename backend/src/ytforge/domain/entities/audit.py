from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AuditLog:
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    ip_address: str | None = None
