from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from ytforge.application.ports.providers import UnitOfWork


@dataclass(frozen=True, slots=True)
class QuotaStatus:
    units_consumed_today: int
    units_budget: int

    @property
    def units_remaining(self) -> int:
        return self.units_budget - self.units_consumed_today

    @property
    def is_exhausted(self) -> bool:
        return self.units_remaining <= 0


async def check_quota_budget(uow: UnitOfWork, channel_id: uuid.UUID, units_budget: int) -> QuotaStatus:
    """Sums today's `api_quota_ledger` rows for the channel against the
    configured daily budget (`settings.youtube.daily_quota_budget`) —
    callers (PublisherAgent) check this before spending more quota rather
    than discovering exhaustion only after YouTube's API rejects the call."""
    today = datetime.now(UTC).date()
    entries = await uow.api_quota_ledger.list_for_channel(channel_id, today, today)
    consumed = sum(e.units_consumed for e in entries)
    return QuotaStatus(units_consumed_today=consumed, units_budget=units_budget)
