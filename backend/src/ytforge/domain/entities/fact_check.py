from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ytforge.domain.enums import FactCheckVerdict


@dataclass(slots=True, kw_only=True)
class FactCheck:
    id: uuid.UUID
    script_id: uuid.UUID
    script_version: int
    verdict: FactCheckVerdict
    created_at: datetime
    updated_at: datetime
    flags: list[Any] = field(default_factory=list)
    model_used: str | None = None
