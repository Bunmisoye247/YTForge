from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from uuid6 import uuid7

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import ApiQuotaLedger


@dataclass(frozen=True, slots=True)
class RecordQuotaUsageInput:
    channel_id: uuid.UUID
    operation: str
    units_consumed: int
    units_budget: int


async def record_quota_usage(uow: UnitOfWork, data: RecordQuotaUsageInput) -> ApiQuotaLedger:
    """One row per API call that spends YouTube quota (ARCHITECTURE.md
    §6.1's api_quota_ledger, §8's "API quota ledger prevents silent quota
    exhaustion"). `units_budget` is snapshotted onto the row so historical
    entries show what the budget was at the time, even if the configured
    budget changes later."""
    entry = ApiQuotaLedger(
        id=uuid7(),
        channel_id=data.channel_id,
        date=datetime.now(UTC).date(),
        operation=data.operation,
        units_consumed=data.units_consumed,
        units_budget=data.units_budget,
    )
    await uow.api_quota_ledger.add(entry)
    await uow.commit()
    return entry
