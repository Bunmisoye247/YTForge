from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Asset
from ytforge.domain.errors import InvalidTransitionError


async def orphan_asset(uow: UnitOfWork, asset_id: uuid.UUID) -> Asset:
    """Soft-deletes an asset. Only called once the ASSET_DELETION approval
    for it has been granted (see `approvals.decide_approval`)."""
    asset = await uow.assets.get_by_id(asset_id)
    if asset is None:
        raise NotFoundError("Asset", asset_id)

    try:
        asset.orphan()
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    asset.updated_at = datetime.now(UTC)

    await uow.assets.update(asset)
    await uow.add_event(
        aggregate_type="asset", aggregate_id=asset.id, event_type="AssetOrphaned", payload={}
    )
    await uow.commit()
    return asset
