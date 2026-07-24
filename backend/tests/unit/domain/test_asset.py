from __future__ import annotations

from datetime import UTC, datetime

import pytest
from uuid6 import uuid7

from ytforge.domain.entities import Asset
from ytforge.domain.enums import AssetStatus, AssetType
from ytforge.domain.errors import InvalidTransitionError


def _make_asset(status: AssetStatus = AssetStatus.PENDING) -> Asset:
    now = datetime.now(UTC)
    return Asset(
        id=uuid7(),
        project_id=uuid7(),
        scene_id=None,
        asset_type=AssetType.IMAGE,
        status=status,
        bucket="raw-assets",
        object_key="p/image/1.png",
        created_at=now,
        updated_at=now,
    )


def test_pending_to_ready() -> None:
    asset = _make_asset(AssetStatus.PENDING)
    asset.mark_ready()
    assert asset.status == AssetStatus.READY


def test_pending_to_failed() -> None:
    asset = _make_asset(AssetStatus.PENDING)
    asset.mark_failed()
    assert asset.status == AssetStatus.FAILED


def test_ready_cannot_mark_failed() -> None:
    asset = _make_asset(AssetStatus.READY)
    with pytest.raises(InvalidTransitionError):
        asset.mark_failed()


def test_ready_can_be_orphaned() -> None:
    asset = _make_asset(AssetStatus.READY)
    asset.orphan()
    assert asset.status == AssetStatus.ORPHANED


def test_orphaned_is_terminal() -> None:
    asset = _make_asset(AssetStatus.ORPHANED)
    with pytest.raises(InvalidTransitionError):
        asset.mark_ready()
