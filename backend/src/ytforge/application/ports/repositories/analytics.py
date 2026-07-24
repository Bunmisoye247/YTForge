from __future__ import annotations

import uuid
from typing import Protocol

from ytforge.domain.entities import (
    AnalyticsDailyMetric,
    AnalyticsRetentionPoint,
    AnalyticsTrafficSource,
)


class AnalyticsDailyMetricRepository(Protocol):
    async def upsert(self, metric: AnalyticsDailyMetric) -> None: ...
    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsDailyMetric]: ...


class AnalyticsRetentionPointRepository(Protocol):
    async def upsert(self, point: AnalyticsRetentionPoint) -> None: ...
    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsRetentionPoint]: ...


class AnalyticsTrafficSourceRepository(Protocol):
    async def upsert(self, source: AnalyticsTrafficSource) -> None: ...
    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsTrafficSource]: ...
