from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_
from decimal import Decimal

import httpx

from ytforge.infrastructure.telemetry.provider_metrics import record_provider_call

_REPORTS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
_METRICS = ("views", "estimatedMinutesWatched", "likes", "comments", "shares", "subscribersGained", "estimatedRevenue")


@dataclass(frozen=True, slots=True)
class AnalyticsMetricsResult:
    views: int = 0
    watch_time_minutes: Decimal = Decimal("0")
    likes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    revenue_usd: Decimal = Decimal("0")


class YouTubeAnalyticsApiClient:
    """Real YouTube Analytics API v2 client (ARCHITECTURE.md §3's
    AnalyticsAgent trigger table: "metrics rows ... YouTube Analytics
    API") — plain httpx, no vendor SDK, matching `YouTubeDataApiGateway`'s
    convention.

    # verify against current API docs: the exact metric-name spelling
    (estimatedMinutesWatched, estimatedRevenue, …) and whether
    `estimatedRevenue` requires a linked AdSense account / monetization
    scope not requested by `GoogleOAuthClient`'s current scope list — both
    worth re-confirming before a real pull. Nothing here can be exercised
    against a real YouTube account in this environment regardless."""

    async def fetch_daily_metrics(self, access_token: str, youtube_video_id: str, target_date: date_) -> AnalyticsMetricsResult:
        async with (
            record_provider_call("youtube_analytics_api", "reports.query"),
            httpx.AsyncClient() as client,
        ):
            response = await client.get(
                _REPORTS_URL,
                params={
                    "ids": "channel==MINE",
                    "startDate": target_date.isoformat(),
                    "endDate": target_date.isoformat(),
                    "metrics": ",".join(_METRICS),
                    "filters": f"video=={youtube_video_id}",
                },
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            body = response.json()

        rows = body.get("rows") or []
        if not rows:
            return AnalyticsMetricsResult()

        headers = [h["name"] for h in body["columnHeaders"]]
        values = dict(zip(headers, rows[0], strict=True))

        return AnalyticsMetricsResult(
            views=int(values.get("views", 0)),
            watch_time_minutes=Decimal(str(values.get("estimatedMinutesWatched", 0))),
            likes=int(values.get("likes", 0)),
            comments=int(values.get("comments", 0)),
            shares=int(values.get("shares", 0)),
            subscribers_gained=int(values.get("subscribersGained", 0)),
            revenue_usd=Decimal(str(values.get("estimatedRevenue", 0))),
        )
