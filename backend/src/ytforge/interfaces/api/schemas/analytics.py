from __future__ import annotations

import uuid
from datetime import date as date_
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyMetricIngestRequest(BaseModel):
    date: date_
    views: int = Field(default=0, ge=0)
    watch_time_minutes: Decimal = Field(default=Decimal("0"), ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    subscribers_gained: int = 0
    revenue_usd: Decimal = Field(default=Decimal("0"), ge=0)


class DailyMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    date: date_
    views: int
    watch_time_minutes: Decimal
    likes: int
    comments: int
    shares: int
    subscribers_gained: int
    revenue_usd: Decimal


class RetentionPointIngestRequest(BaseModel):
    date: date_
    elapsed_video_percent: Decimal = Field(ge=0, le=100)
    audience_retention_percent: Decimal = Field(ge=0, le=100)


class RetentionPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    date: date_
    elapsed_video_percent: Decimal
    audience_retention_percent: Decimal


class TrafficSourceIngestRequest(BaseModel):
    date: date_
    source_type: str = Field(min_length=1, max_length=64)
    views: int = Field(default=0, ge=0)
    watch_time_minutes: Decimal = Field(default=Decimal("0"), ge=0)


class TrafficSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    video_id: uuid.UUID
    date: date_
    source_type: str
    views: int
    watch_time_minutes: Decimal


class VideoAnalyticsRead(BaseModel):
    daily_metrics: list[DailyMetricRead]
    retention_points: list[RetentionPointRead]
    traffic_sources: list[TrafficSourceRead]
