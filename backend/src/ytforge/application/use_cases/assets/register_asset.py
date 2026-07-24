from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import Asset
from ytforge.domain.enums import AssetStatus, AssetType


@dataclass(frozen=True, slots=True)
class RegisterAssetInput:
    project_id: uuid.UUID
    asset_type: AssetType
    bucket: str
    object_key: str
    scene_id: uuid.UUID | None = None
    checksum_sha256: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)


async def register_asset(uow: UnitOfWork, data: RegisterAssetInput) -> Asset:
    if await uow.projects.get_by_id(data.project_id) is None:
        raise NotFoundError("Project", data.project_id)

    now = datetime.now(UTC)
    asset = Asset(
        id=uuid7(),
        project_id=data.project_id,
        scene_id=data.scene_id,
        asset_type=data.asset_type,
        status=AssetStatus.PENDING,
        bucket=data.bucket,
        object_key=data.object_key,
        checksum_sha256=data.checksum_sha256,
        provenance=data.provenance,
        created_at=now,
        updated_at=now,
    )
    await uow.assets.add(asset)
    await uow.commit()
    return asset
