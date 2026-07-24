from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Asset


class AssetRepository(Protocol):
    async def get_by_id(self, asset_id: uuid.UUID) -> Asset | None: ...
    async def add(self, asset: Asset) -> None: ...
    async def update(self, asset: Asset) -> None: ...
    async def list_for_project(self, project_id: uuid.UUID, params: PageParams) -> Page[Asset]: ...
