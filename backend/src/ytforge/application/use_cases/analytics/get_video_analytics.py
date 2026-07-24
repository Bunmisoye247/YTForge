from __future__ import annotations

import uuid
from dataclasses import dataclass

from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import (
    AnalyticsDailyMetric,
    AnalyticsRetentionPoint,
    AnalyticsTrafficSource,
)


@dataclass(frozen=True, slots=True)
class VideoAnalytics:
    daily_metrics: list[AnalyticsDailyMetric]
    retention_points: list[AnalyticsRetentionPoint]
    traffic_sources: list[AnalyticsTrafficSource]


async def get_video_analytics(uow: UnitOfWork, video_id: uuid.UUID) -> VideoAnalytics:
    return VideoAnalytics(
        daily_metrics=await uow.analytics_daily_metrics.list_for_video(video_id),
        retention_points=await uow.analytics_retention_points.list_for_video(video_id),
        traffic_sources=await uow.analytics_traffic_sources.list_for_video(video_id),
    )
