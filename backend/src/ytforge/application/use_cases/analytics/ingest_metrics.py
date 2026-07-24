from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date as date_
from decimal import Decimal

from uuid6 import uuid7

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.domain.entities import (
    AnalyticsDailyMetric,
    AnalyticsRetentionPoint,
    AnalyticsTrafficSource,
)


@dataclass(frozen=True, slots=True)
class IngestDailyMetricInput:
    video_id: uuid.UUID
    date: date_
    views: int = 0
    watch_time_minutes: Decimal = Decimal("0")
    likes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    revenue_usd: Decimal = Decimal("0")


async def ingest_daily_metric(uow: UnitOfWork, data: IngestDailyMetricInput) -> AnalyticsDailyMetric:
    """Manual/CSV ingestion path — automated YouTube Analytics API ingestion
    is added in Phase 8 alongside the AnalyticsAgent."""
    if await uow.videos.get_by_id(data.video_id) is None:
        raise NotFoundError("Video", data.video_id)

    metric = AnalyticsDailyMetric(
        id=uuid7(),
        video_id=data.video_id,
        date=data.date,
        views=data.views,
        watch_time_minutes=data.watch_time_minutes,
        likes=data.likes,
        comments=data.comments,
        shares=data.shares,
        subscribers_gained=data.subscribers_gained,
        revenue_usd=data.revenue_usd,
    )
    await uow.analytics_daily_metrics.upsert(metric)
    await uow.commit()
    return metric


@dataclass(frozen=True, slots=True)
class IngestRetentionPointInput:
    video_id: uuid.UUID
    date: date_
    elapsed_video_percent: Decimal
    audience_retention_percent: Decimal


async def ingest_retention_point(
    uow: UnitOfWork, data: IngestRetentionPointInput
) -> AnalyticsRetentionPoint:
    if await uow.videos.get_by_id(data.video_id) is None:
        raise NotFoundError("Video", data.video_id)

    point = AnalyticsRetentionPoint(
        id=uuid7(),
        video_id=data.video_id,
        date=data.date,
        elapsed_video_percent=data.elapsed_video_percent,
        audience_retention_percent=data.audience_retention_percent,
    )
    await uow.analytics_retention_points.upsert(point)
    await uow.commit()
    return point


@dataclass(frozen=True, slots=True)
class IngestTrafficSourceInput:
    video_id: uuid.UUID
    date: date_
    source_type: str
    views: int = 0
    watch_time_minutes: Decimal = Decimal("0")


async def ingest_traffic_source(
    uow: UnitOfWork, data: IngestTrafficSourceInput
) -> AnalyticsTrafficSource:
    if await uow.videos.get_by_id(data.video_id) is None:
        raise NotFoundError("Video", data.video_id)

    source = AnalyticsTrafficSource(
        id=uuid7(),
        video_id=data.video_id,
        date=data.date,
        source_type=data.source_type,
        views=data.views,
        watch_time_minutes=data.watch_time_minutes,
    )
    await uow.analytics_traffic_sources.upsert(source)
    await uow.commit()
    return source
