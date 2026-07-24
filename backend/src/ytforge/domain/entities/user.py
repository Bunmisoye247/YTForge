from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    id: uuid.UUID
    email: str
    hashed_password: str
    full_name: str
    is_active: bool
    is_superuser: bool
    token_version: int
    created_at: datetime
    updated_at: datetime
