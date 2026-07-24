from __future__ import annotations

import pytest
from uuid6 import uuid7

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.use_cases.quota import (
    RecordQuotaUsageInput,
    check_quota_budget,
    record_quota_usage,
)


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def test_check_quota_budget_with_no_usage_reports_full_budget(uow: FakeUnitOfWork) -> None:
    channel_id = uuid7()

    status = await check_quota_budget(uow, channel_id, units_budget=10000)

    assert status.units_consumed_today == 0
    assert status.units_remaining == 10000
    assert not status.is_exhausted


async def test_record_quota_usage_then_check_reflects_it(uow: FakeUnitOfWork) -> None:
    channel_id = uuid7()

    await record_quota_usage(
        uow,
        RecordQuotaUsageInput(channel_id=channel_id, operation="videos.insert", units_consumed=1600, units_budget=10000),
    )
    status = await check_quota_budget(uow, channel_id, units_budget=10000)

    assert status.units_consumed_today == 1600
    assert status.units_remaining == 8400
    assert not status.is_exhausted


async def test_check_quota_budget_reports_exhausted_when_over_budget(uow: FakeUnitOfWork) -> None:
    channel_id = uuid7()
    await record_quota_usage(
        uow,
        RecordQuotaUsageInput(channel_id=channel_id, operation="videos.insert", units_consumed=10000, units_budget=10000),
    )

    status = await check_quota_budget(uow, channel_id, units_budget=10000)

    assert status.is_exhausted
    assert status.units_remaining == 0


async def test_quota_usage_is_scoped_per_channel(uow: FakeUnitOfWork) -> None:
    channel_a, channel_b = uuid7(), uuid7()
    await record_quota_usage(
        uow, RecordQuotaUsageInput(channel_id=channel_a, operation="videos.insert", units_consumed=5000, units_budget=10000)
    )

    status_a = await check_quota_budget(uow, channel_a, units_budget=10000)
    status_b = await check_quota_budget(uow, channel_b, units_budget=10000)

    assert status_a.units_consumed_today == 5000
    assert status_b.units_consumed_today == 0
