from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Asset
from ytforge.infrastructure.db.models import Asset as AssetOrm
from ytforge.infrastructure.db.repositories._pagination import paginate


def _to_domain(row: AssetOrm) -> Asset:
    return Asset(
        id=row.id,
        project_id=row.project_id,
        scene_id=row.scene_id,
        asset_type=row.asset_type,
        status=row.status,
        bucket=row.bucket,
        object_key=row.object_key,
        checksum_sha256=row.checksum_sha256,
        provenance=row.provenance,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyAssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, asset_id: uuid.UUID) -> Asset | None:
        row = await self._session.get(AssetOrm, asset_id)
        return _to_domain(row) if row is not None else None

    async def add(self, asset: Asset) -> None:
        row = AssetOrm(
            id=asset.id,
            project_id=asset.project_id,
            scene_id=asset.scene_id,
            asset_type=asset.asset_type,
            status=asset.status,
            bucket=asset.bucket,
            object_key=asset.object_key,
            checksum_sha256=asset.checksum_sha256,
            provenance=asset.provenance,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, asset: Asset) -> None:
        row = await self._session.get(AssetOrm, asset.id)
        assert row is not None
        row.status = asset.status
        row.checksum_sha256 = asset.checksum_sha256
        row.provenance = asset.provenance
        row.updated_at = asset.updated_at
        await self._session.flush()

    async def list_for_project(self, project_id: uuid.UUID, params: PageParams) -> Page[Asset]:
        stmt = (
            select(AssetOrm)
            .where(AssetOrm.project_id == project_id)
            .order_by(AssetOrm.created_at.desc())
        )
        return await paginate(self._session, stmt, params, _to_domain)
