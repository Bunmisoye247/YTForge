from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.application.common.pagination import Page, PageParams
from ytforge.domain.entities import Trend


class TrendRepository(Protocol):
    async def get_by_id(self, trend_id: uuid.UUID) -> Trend | None: ...
    async def add(self, trend: Trend) -> None: ...
    async def list_for_channel(
        self, channel_id: uuid.UUID, params: PageParams
    ) -> Page[Trend]: ...
