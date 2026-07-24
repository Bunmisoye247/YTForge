from __future__ import annotations

import uuid
from datetime import date as date_
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ytforge.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from ytforge.infrastructure.db.models.videos import Video


class AnalyticsDailyMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_daily_metrics"
    __table_args__ = (
        UniqueConstraint("video_id", "date", name="uq_analytics_daily_metrics_video_date"),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watch_time_minutes: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subscribers_gained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    video: Mapped[Video] = relationship()


class AnalyticsRetentionPoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_retention_points"
    __table_args__ = (
        UniqueConstraint(
            "video_id", "date", "elapsed_video_percent", name="uq_analytics_retention_video_date_pct"
        ),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    elapsed_video_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    audience_retention_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    video: Mapped[Video] = relationship()


class AnalyticsTrafficSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_traffic_sources"
    __table_args__ = (
        UniqueConstraint(
            "video_id", "date", "source_type", name="uq_analytics_traffic_video_date_source"
        ),
    )

    video_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    watch_time_minutes: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    video: Mapped[Video] = relationship()
