from __future__ import annotations

import uuid
from datetime import UTC, datetime

from ytforge.application.common.errors import InvalidStateError, NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Asset
from ytforge.domain.errors import InvalidTransitionError


async def mark_asset_ready(uow: UnitOfWork, asset_id: uuid.UUID) -> Asset:
    asset = await _get_asset(uow, asset_id)
    try:
        asset.mark_ready()
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    return await _save(uow, asset)


async def mark_asset_failed(uow: UnitOfWork, asset_id: uuid.UUID) -> Asset:
    asset = await _get_asset(uow, asset_id)
    try:
        asset.mark_failed()
    except InvalidTransitionError as exc:
        raise InvalidStateError(exc) from exc
    return await _save(uow, asset)


async def _get_asset(uow: UnitOfWork, asset_id: uuid.UUID) -> Asset:
    asset = await uow.assets.get_by_id(asset_id)
    if asset is None:
        raise NotFoundError("Asset", asset_id)
    return asset


async def _save(uow: UnitOfWork, asset: Asset) -> Asset:
    asset.updated_at = datetime.now(UTC)
    await uow.assets.update(asset)
    await uow.commit()
    return asset
