from __future__ import annotations

import uuid
from datetime import date as date_
from typing import Protocol

from ytforge.domain.entities import ApiQuotaLedger


class ApiQuotaLedgerRepository(Protocol):
    async def list_for_channel(
        self, channel_id: uuid.UUID, start: date_, end: date_
    ) -> list[ApiQuotaLedger]: ...
    async def add(self, entry: ApiQuotaLedger) -> None: ...
