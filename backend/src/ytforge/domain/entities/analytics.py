from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date as date_
from decimal import Decimal


@dataclass(slots=True)
class AnalyticsDailyMetric:
    id: uuid.UUID
    video_id: uuid.UUID
    date: date_
    views: int = 0
    watch_time_minutes: Decimal = Decimal("0")
    likes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    revenue_usd: Decimal = Decimal("0")


@dataclass(slots=True)
class AnalyticsRetentionPoint:
    id: uuid.UUID
    video_id: uuid.UUID
    date: date_
    elapsed_video_percent: Decimal
    audience_retention_percent: Decimal


@dataclass(slots=True)
class AnalyticsTrafficSource:
    id: uuid.UUID
    video_id: uuid.UUID
    date: date_
    source_type: str
    views: int = 0
    watch_time_minutes: Decimal = Decimal("0")
