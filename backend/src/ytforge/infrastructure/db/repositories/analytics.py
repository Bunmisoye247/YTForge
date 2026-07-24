from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ytforge.domain.entities import (
    AnalyticsDailyMetric,
    AnalyticsRetentionPoint,
    AnalyticsTrafficSource,
)
from ytforge.infrastructure.db.models import AnalyticsDailyMetric as DailyMetricOrm
from ytforge.infrastructure.db.models import AnalyticsRetentionPoint as RetentionPointOrm
from ytforge.infrastructure.db.models import AnalyticsTrafficSource as TrafficSourceOrm


def _daily_to_domain(row: DailyMetricOrm) -> AnalyticsDailyMetric:
    return AnalyticsDailyMetric(
        id=row.id,
        video_id=row.video_id,
        date=row.date,
        views=row.views,
        watch_time_minutes=row.watch_time_minutes,
        likes=row.likes,
        comments=row.comments,
        shares=row.shares,
        subscribers_gained=row.subscribers_gained,
        revenue_usd=row.revenue_usd,
    )


def _retention_to_domain(row: RetentionPointOrm) -> AnalyticsRetentionPoint:
    return AnalyticsRetentionPoint(
        id=row.id,
        video_id=row.video_id,
        date=row.date,
        elapsed_video_percent=row.elapsed_video_percent,
        audience_retention_percent=row.audience_retention_percent,
    )


def _traffic_to_domain(row: TrafficSourceOrm) -> AnalyticsTrafficSource:
    return AnalyticsTrafficSource(
        id=row.id,
        video_id=row.video_id,
        date=row.date,
        source_type=row.source_type,
        views=row.views,
        watch_time_minutes=row.watch_time_minutes,
    )


class SqlAlchemyAnalyticsDailyMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, metric: AnalyticsDailyMetric) -> None:
        stmt = select(DailyMetricOrm).where(
            DailyMetricOrm.video_id == metric.video_id, DailyMetricOrm.date == metric.date
        )
        row = await self._session.scalar(stmt)
        if row is None:
            row = DailyMetricOrm(id=metric.id, video_id=metric.video_id, date=metric.date)
            self._session.add(row)
        row.views = metric.views
        row.watch_time_minutes = metric.watch_time_minutes
        row.likes = metric.likes
        row.comments = metric.comments
        row.shares = metric.shares
        row.subscribers_gained = metric.subscribers_gained
        row.revenue_usd = metric.revenue_usd
        await self._session.flush()

    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsDailyMetric]:
        stmt = select(DailyMetricOrm).where(DailyMetricOrm.video_id == video_id).order_by(DailyMetricOrm.date)
        rows = await self._session.scalars(stmt)
        return [_daily_to_domain(row) for row in rows]


class SqlAlchemyAnalyticsRetentionPointRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, point: AnalyticsRetentionPoint) -> None:
        stmt = select(RetentionPointOrm).where(
            RetentionPointOrm.video_id == point.video_id,
            RetentionPointOrm.date == point.date,
            RetentionPointOrm.elapsed_video_percent == point.elapsed_video_percent,
        )
        row = await self._session.scalar(stmt)
        if row is None:
            row = RetentionPointOrm(
                id=point.id,
                video_id=point.video_id,
                date=point.date,
                elapsed_video_percent=point.elapsed_video_percent,
            )
            self._session.add(row)
        row.audience_retention_percent = point.audience_retention_percent
        await self._session.flush()

    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsRetentionPoint]:
        stmt = (
            select(RetentionPointOrm)
            .where(RetentionPointOrm.video_id == video_id)
            .order_by(RetentionPointOrm.date, RetentionPointOrm.elapsed_video_percent)
        )
        rows = await self._session.scalars(stmt)
        return [_retention_to_domain(row) for row in rows]


class SqlAlchemyAnalyticsTrafficSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, source: AnalyticsTrafficSource) -> None:
        stmt = select(TrafficSourceOrm).where(
            TrafficSourceOrm.video_id == source.video_id,
            TrafficSourceOrm.date == source.date,
            TrafficSourceOrm.source_type == source.source_type,
        )
        row = await self._session.scalar(stmt)
        if row is None:
            row = TrafficSourceOrm(
                id=source.id,
                video_id=source.video_id,
                date=source.date,
                source_type=source.source_type,
            )
            self._session.add(row)
        row.views = source.views
        row.watch_time_minutes = source.watch_time_minutes
        await self._session.flush()

    async def list_for_video(self, video_id: uuid.UUID) -> list[AnalyticsTrafficSource]:
        stmt = (
            select(TrafficSourceOrm)
            .where(TrafficSourceOrm.video_id == video_id)
            .order_by(TrafficSourceOrm.date)
        )
        rows = await self._session.scalars(stmt)
        return [_traffic_to_domain(row) for row in rows]
