from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from fixtures.fakes import FakeUnitOfWork
from ytforge.application.common.errors import InvalidStateError
from ytforge.application.use_cases.approvals import DecideApprovalInput, decide_approval
from ytforge.application.use_cases.assets import request_asset_deletion
from ytforge.domain.entities import Asset
from ytforge.domain.enums import ApprovalStatus, AssetStatus, AssetType


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


async def _seed_ready_asset(uow: FakeUnitOfWork) -> Asset:
    now = datetime.now(UTC)
    asset = Asset(
        id=uuid7(),
        project_id=uuid7(),
        scene_id=None,
        asset_type=AssetType.IMAGE,
        status=AssetStatus.READY,
        bucket="raw-assets",
        object_key="p/image/1.png",
        created_at=now,
        updated_at=now,
    )
    await uow.assets.add(asset)
    return asset


async def test_decide_approval_approved_orphans_the_asset(uow: FakeUnitOfWork) -> None:
    asset = await _seed_ready_asset(uow)
    approval = await request_asset_deletion(uow, asset.id, uuid7())

    decided = await decide_approval(
        uow, approval.id, DecideApprovalInput(status=ApprovalStatus.APPROVED, decided_by_user_id=uuid7())
    )

    assert decided.status == ApprovalStatus.APPROVED
    stored_asset = await uow.assets.get_by_id(asset.id)
    assert stored_asset is not None
    assert stored_asset.status == AssetStatus.ORPHANED
    assert any(e["event_type"] == "ApprovalGranted" for e in uow.events)


async def test_decide_approval_rejected_leaves_asset_untouched(uow: FakeUnitOfWork) -> None:
    asset = await _seed_ready_asset(uow)
    approval = await request_asset_deletion(uow, asset.id, uuid7())

    await decide_approval(
        uow, approval.id, DecideApprovalInput(status=ApprovalStatus.REJECTED, decided_by_user_id=uuid7())
    )

    stored_asset = await uow.assets.get_by_id(asset.id)
    assert stored_asset is not None
    assert stored_asset.status == AssetStatus.READY


async def test_decide_approval_twice_rejected(uow: FakeUnitOfWork) -> None:
    asset = await _seed_ready_asset(uow)
    approval = await request_asset_deletion(uow, asset.id, uuid7())
    await decide_approval(
        uow, approval.id, DecideApprovalInput(status=ApprovalStatus.APPROVED, decided_by_user_id=uuid7())
    )

    with pytest.raises(InvalidStateError):
        await decide_approval(
            uow,
            approval.id,
            DecideApprovalInput(status=ApprovalStatus.REJECTED, decided_by_user_id=uuid7()),
        )
