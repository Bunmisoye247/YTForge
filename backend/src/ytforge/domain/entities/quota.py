from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date as date_


@dataclass(slots=True)
class ApiQuotaLedger:
    id: uuid.UUID
    channel_id: uuid.UUID
    date: date_
    operation: str
    units_consumed: int
    units_budget: int
