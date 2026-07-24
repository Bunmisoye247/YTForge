from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ytforge.application.common.errors import NotFoundError
from ytforge.application.ports.providers import UnitOfWork
from ytforge.application.use_cases.analytics import (
    IngestDailyMetricInput,
    IngestRetentionPointInput,
    IngestTrafficSourceInput,
    get_video_analytics,
    ingest_daily_metric,
    ingest_retention_point,
    ingest_traffic_source,
)
from ytforge.interfaces.api.deps.auth import CurrentUser
from ytforge.interfaces.api.deps.db import get_uow
from ytforge.interfaces.api.schemas.analytics import (
    DailyMetricIngestRequest,
    DailyMetricRead,
    RetentionPointIngestRequest,
    RetentionPointRead,
    TrafficSourceIngestRequest,
    TrafficSourceRead,
    VideoAnalyticsRead,
)

router = APIRouter(prefix="/videos/{video_id}/analytics", tags=["analytics"])


@router.get("", response_model=VideoAnalyticsRead)
async def get_(
    video_id: uuid.UUID, user: CurrentUser, uow: Annotated[UnitOfWork, Depends(get_uow)]
) -> VideoAnalyticsRead:
    analytics = await get_video_analytics(uow, video_id)
    return VideoAnalyticsRead(
        daily_metrics=[DailyMetricRead.model_validate(m) for m in analytics.daily_metrics],
        retention_points=[RetentionPointRead.model_validate(p) for p in analytics.retention_points],
        traffic_sources=[TrafficSourceRead.model_validate(s) for s in analytics.traffic_sources],
    )


@router.post("/daily-metrics", response_model=DailyMetricRead, status_code=status.HTTP_201_CREATED)
async def ingest_daily(
    video_id: uuid.UUID,
    data: DailyMetricIngestRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> DailyMetricRead:
    try:
        metric = await ingest_daily_metric(
            uow,
            IngestDailyMetricInput(
                video_id=video_id,
                date=data.date,
                views=data.views,
                watch_time_minutes=data.watch_time_minutes,
                likes=data.likes,
                comments=data.comments,
                shares=data.shares,
                subscribers_gained=data.subscribers_gained,
                revenue_usd=data.revenue_usd,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return DailyMetricRead.model_validate(metric)


@router.post(
    "/retention-points", response_model=RetentionPointRead, status_code=status.HTTP_201_CREATED
)
async def ingest_retention(
    video_id: uuid.UUID,
    data: RetentionPointIngestRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> RetentionPointRead:
    try:
        point = await ingest_retention_point(
            uow,
            IngestRetentionPointInput(
                video_id=video_id,
                date=data.date,
                elapsed_video_percent=data.elapsed_video_percent,
                audience_retention_percent=data.audience_retention_percent,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return RetentionPointRead.model_validate(point)


@router.post(
    "/traffic-sources", response_model=TrafficSourceRead, status_code=status.HTTP_201_CREATED
)
async def ingest_traffic(
    video_id: uuid.UUID,
    data: TrafficSourceIngestRequest,
    user: CurrentUser,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> TrafficSourceRead:
    try:
        source = await ingest_traffic_source(
            uow,
            IngestTrafficSourceInput(
                video_id=video_id,
                date=data.date,
                source_type=data.source_type,
                views=data.views,
                watch_time_minutes=data.watch_time_minutes,
            ),
        )
    except NotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return TrafficSourceRead.model_validate(source)
